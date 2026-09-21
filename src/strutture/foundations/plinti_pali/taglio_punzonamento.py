"""Step 4: beam shear and punching design (EC2 §6.2.2, §6.4) — docs/specs/fond-plinti-pali.md Tool-4.

Fixes (docs/architecture-batch2.md §7):
- `AR99` (`k`): the sheet never clamps `k = 1+sqrt(200/d)` at EC2's required ceiling of 2.0;
  `legacy_compat=True` reproduces the unclamped value, the fix uses `shared.ec2_shear.k_size`.
- `AR100` (`rho`): the sheet divides the bottom reinforcement's `mm²/m` figure by the FULL plinth
  width `b` (`As_real/(AX*d)`), effectively treating a per-meter density as if it were a total area
  spread over `AX` millimetres — a unit mismatch that understates `rho` by a factor `AX/1000` (here
  4x). The fix divides by the 1-meter design-strip width the reinforcement was actually computed
  for (`As_real/(1000*d)`); `legacy_compat=True` reproduces the sheet's `b`-width division.
- `AR90` ("As_real,tot", described in the spec as a separate lever-arm sub-calc): tracing the actual
  formula (`Footing check!AR100 = AV28/(AR60*AR86)`) shows `rho` is built directly from `AV28`
  (the `flessione.inf_x.as_prov_mm2` this step already has) — the mysterious `AR90` never enters it.

Code-review fixes (docs review, not in the architecture bug list; all gated on `legacy_compat=False`
so the sheet reproduction is untouched):
- `d_mm <= 0` now raises `CalcError` (was a bare `ValueError`, uncaught by `shared.tool.execute`).
- EC2 §6.2.2(6): `av` is clamped to `[0.5d, 2d]` before forming β = av/(2d) (β ∈ [0.25, 1.0]) instead
  of letting an unphysically small `av` crater the reduced shear demand.
- EC2 eq. 6.5's companion crushing check `VEd <= 0.5*b*d*ν*fcd` at the column/pile face is now
  computed and enters `verificato`.
- `punzonamento_colonna`: `alpha_cc` is now `shared.materials.concrete.ALPHA_CC` (0.85, NTC2018
  §4.1.2.1.1.1) instead of a hard-coded 1.0, and the eccentricity factor β (EC2 §6.4.3, eq. 6.39
  simplified for an interior column) multiplies `NSd` instead of assuming β=1.
- Both `taglio`'s eq. 6.5 companion crushing check and `punzonamento_colonna`'s own vRd,max now take
  the vRd,max coefficient (`coeff_vrd_max` on `PlintoSuPaliInput`, docs/divergences/ec2-shared.md) as
  an explicit user choice (0.4 EN 1992-1-1/A1:2014 default, or 0.5 EN 1992-1-1:2004 + Appendice
  Nazionale italiana) in `legacy_compat=False` mode; `legacy_compat=True` keeps the sheet's own `0.5`
  coefficient with `alpha_cc=1.0` unconditionally (this pile-cap workbook's own combination), ignoring
  `coeff_vrd_max`.
- `punzonamento_palo`: the 2d control perimeter is capped where it would overlap the cap edge or a
  neighbouring pile's own cone (EC2 §6.4.2(5)); when the available distance `a` is < 2d, `v_rd_c`'s
  `av_over_2d` enhancement (§6.4.4(2)) is used instead of the unreduced formula."""
import math

from strutture.shared.divergences import legacy
from strutture.shared.ec2_shear import control_perimeter, k_size, v_rd_c, v_rd_max
from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.materials.concrete import ALPHA_CC
from strutture.shared.numeric import clamp
from strutture.shared.report import CalcError

from .models_taglio import Punzonamento, PunzonamentoPalo, Taglio

MARGIN_EFFECTIVE_DEPTH_FACTOR = 2.0  # sheet's `d = H - cover - 2*øl` (Tool4's own, coarser than Tool2's 1.5*ø).
STRIP_WIDTH_MM = 1000.0  # the 1m design strip `flessione.py` computed `as_prov_mm2` for.
PUNCHING_COEFFICIENT_COLUMN_FACE = 0.5  # sheet's own coefficient in front of nu*fcd at u0 (legacy_compat=True only).
VED_MAX_COEFFICIENT = 0.5  # sheet-adjacent coefficient for the companion crushing check (legacy_compat=True only).
AV_MIN_FACTOR = 0.5  # EC2 §6.2.2(6): "for av < 0.5d the value av = 0.5d should be used".
AV_MAX_FACTOR = 2.0  # beyond av=2d the reduction no longer applies (beta capped at 1.0).
BETA_ECCENTRICITY_COEFFICIENT = 1.8  # EC2 eq. 6.39, simplified interior-column approximation.


def taglio(
    n_totale_max_kN: float, peso_proprio_kN: float, ax_mm: float, h_plinto_mm: float, copriferro_mm: float,
    diametro_long_assunto_mm: float, av_mm: float, as_prov_x_mm2: float, fck_MPa: float, gamma_c: float,
    *, legacy_compat: bool, coeff_vrd_max: float = V_RD_MAX_COEFF_A1_2014,
) -> Taglio:
    """Beam shear at the reduced distance `av` from the pile face."""
    d_mm = h_plinto_mm - copriferro_mm - MARGIN_EFFECTIVE_DEPTH_FACTOR * diametro_long_assunto_mm
    if d_mm <= 0:
        raise CalcError(f"copriferro/diametro troppo grandi: altezza utile d={d_mm} mm non positiva")
    nsd_kN = n_totale_max_kN + peso_proprio_kN
    ved_kN = nsd_kN / 2.0
    av_eff_mm = (
        av_mm if legacy("plinti-pali/taglio-riduzione-av-senza-limite-inferiore", legacy_compat)
        else clamp(av_mm, AV_MIN_FACTOR * d_mm, AV_MAX_FACTOR * d_mm)
    )
    ved_ridotto_kN = ved_kN * av_eff_mm / (2.0 * d_mm)
    k = (
        (1.0 + (200.0 / d_mm) ** 0.5) if legacy("plinti-pali/coefficiente-k-taglio-non-limitato-a-2", legacy_compat)
        else k_size(d_mm)
    )
    larghezza_rho_mm = (
        ax_mm if legacy("plinti-pali/rho-taglio-divisa-per-larghezza-piena-plinto", legacy_compat) else STRIP_WIDTH_MM
    )
    rho = as_prov_x_mm2 / (larghezza_rho_mm * d_mm)
    vrd_c = v_rd_c(k, rho, fck_MPa, sigma_cp_MPa=0.0, gamma_c=gamma_c)
    vrd_c_kN = vrd_c.v_rd_c_MPa * ax_mm * d_mm / 1000.0
    # Same coefficiente-vrd-max-taglio-punzonamento choice as punzonamento_colonna below: the sheet's
    # alpha_cc=1.0 is coupled with its own coefficient=0.5 for this eq. 6.5 companion check too.
    alpha_cc = 1.0 if legacy("plinti-pali/coefficiente-vrd-max-taglio-punzonamento", legacy_compat) else ALPHA_CC
    coefficient = (
        VED_MAX_COEFFICIENT if legacy("plinti-pali/coefficiente-vrd-max-taglio-punzonamento", legacy_compat)
        else coeff_vrd_max
    )
    vrd_max = v_rd_max(fck_MPa, gamma_c, alpha_cc=alpha_cc, coefficient=coefficient)
    ved_max_kN = vrd_max.v_rd_max_MPa * ax_mm * d_mm / 1000.0
    verificato = (
        ved_ridotto_kN <= vrd_c_kN if legacy("plinti-pali/taglio-verifica-equazione-6-5-mancante", legacy_compat)
        else (ved_ridotto_kN <= vrd_c_kN and ved_kN <= ved_max_kN)
    )
    return Taglio(
        d_mm=d_mm, ved_kN=ved_kN, ved_ridotto_kN=ved_ridotto_kN, k=k, rho=rho, vrd_c_MPa=vrd_c.v_rd_c_MPa,
        vrd_c_kN=vrd_c_kN, ved_max_kN=ved_max_kN, utilizzo=ved_ridotto_kN / vrd_c_kN, verificato=verificato,
    )


def _beta_eccentricita(nsd_kN: float, mx_kNm: float, my_kNm: float, bx_mm: float, by_mm: float) -> float:
    """EC2 §6.4.3(3)/eq. 6.39, simplified formula for an interior column with biaxial eccentricity
    (no exact `u1` shape factor available at this stage, so `beta>=1` is an approximation)."""
    if nsd_kN <= 0:
        return 1.0
    ex_mm = abs(my_kNm) / nsd_kN * 1000.0  # eccentricity along X, from bending about Y (My).
    ey_mm = abs(mx_kNm) / nsd_kN * 1000.0  # eccentricity along Y, from bending about X (Mx).
    return 1.0 + BETA_ECCENTRICITY_COEFFICIENT * math.sqrt((ex_mm / bx_mm) ** 2 + (ey_mm / by_mm) ** 2)


def punzonamento_colonna(
    nsd_kN: float, mx_kNm: float, my_kNm: float, d_mm: float, bx_mm: float, by_mm: float, lx_m: float, ly_m: float,
    diametro_pila_mm: float, fck_MPa: float, gamma_c: float, *, legacy_compat: bool,
    coeff_vrd_max: float = V_RD_MAX_COEFF_A1_2014,
) -> Punzonamento:
    """Column-face punching (§6.4.5) + the sheet's own pile-spacing gate for individual pile cones."""
    perimetro = control_perimeter("rett", bx_mm, by_mm, dist_mm=0.0)
    alpha_cc = 1.0 if legacy("plinti-pali/punzonamento-colonna-alpha-cc-fisso-a-1", legacy_compat) else ALPHA_CC
    coefficient = (
        PUNCHING_COEFFICIENT_COLUMN_FACE
        if legacy("plinti-pali/coefficiente-vrd-max-taglio-punzonamento", legacy_compat) else coeff_vrd_max
    )
    vrd_max = v_rd_max(fck_MPa, gamma_c, alpha_cc=alpha_cc, coefficient=coefficient)
    vrd_max_kN = vrd_max.v_rd_max_MPa * perimetro.u_mm * d_mm / 1000.0
    beta = (
        1.0 if legacy("plinti-pali/punzonamento-colonna-beta-eccentricita-ignorata", legacy_compat)
        else _beta_eccentricita(nsd_kN, mx_kNm, my_kNm, bx_mm, by_mm)
    )
    ved_kN = beta * nsd_kN
    return Punzonamento(
        u_mm=perimetro.u_mm, beta=beta, ved_kN=ved_kN, vrd_max_kN=vrd_max_kN,
        utilizzo=ved_kN / vrd_max_kN, verificato=ved_kN <= vrd_max_kN,
        interasse_x_sufficiente=lx_m * 1000.0 > 3.0 * diametro_pila_mm,
        interasse_y_sufficiente=ly_m * 1000.0 > 3.0 * diametro_pila_mm,
    )


def _distanza_disponibile_mm(
    d_mm: float, diametro_pila_mm: float, lx_m: float, ly_m: float, ax_m: float, by_m: float,
    count_x: int, count_y: int,
) -> float:
    """Largest distance `a` (from the pile face) available in every direction before the 2d control
    perimeter would overlap a neighbouring pile's own cone (mid-distance plane) or the cap edge
    (EC2 §6.4.2(5)): min(2d, clear distance to the nearest such boundary). Isotropic simplification —
    the true non-overlapping perimeter is direction-dependent, this uses the tightest direction for
    the whole circle, which never overstates `u` (conservative)."""
    r_pila_mm = diametro_pila_mm / 2.0
    limiti = [2.0 * d_mm]
    if count_x >= 2:
        limiti.append(lx_m * 1000.0 / 2.0 - r_pila_mm)
    if count_y >= 2:
        limiti.append(ly_m * 1000.0 / 2.0 - r_pila_mm)
    margine_x_mm = (ax_m * 1000.0 - (count_x - 1) * lx_m * 1000.0) / 2.0
    margine_y_mm = (by_m * 1000.0 - (count_y - 1) * ly_m * 1000.0) / 2.0
    limiti.append(margine_x_mm - r_pila_mm)
    limiti.append(margine_y_mm - r_pila_mm)
    return min(limiti)


def punzonamento_palo(
    n_max_pila_kN: float, d_mm: float, diametro_pila_mm: float, rho: float, k: float,
    fck_MPa: float, gamma_c: float, *, lx_m: float, ly_m: float, ax_m: float, by_m: float,
    count_x: int, count_y: int, legacy_compat: bool,
) -> PunzonamentoPalo:
    """Punching of the governing pile at its own control perimeter (task addition, no sheet cell);
    the perimeter is capped to the non-overlapping distance in normal mode (see `_distanza_disponibile_mm`)."""
    if legacy("plinti-pali/punzonamento-palo-perimetro-non-limitato-interasse", legacy_compat):
        a_mm = 2.0 * d_mm
    else:
        a_mm = _distanza_disponibile_mm(d_mm, diametro_pila_mm, lx_m, ly_m, ax_m, by_m, count_x, count_y)
        if a_mm <= 0:
            raise CalcError(
                "punzonamento del palo: interasse pali o distanza dal bordo plinto insufficiente "
                "a definire un perimetro di verifica",
            )
    perimetro = control_perimeter("circ", diametro_pila_mm, None, dist_mm=a_mm)
    k_eff = k_size(d_mm) if k > 2.0 else k
    av_over_2d = (
        None
        if legacy("plinti-pali/punzonamento-palo-perimetro-non-limitato-interasse", legacy_compat) or a_mm >= 2.0 * d_mm
        else a_mm / (2.0 * d_mm)
    )
    vrd_c = v_rd_c(k_eff, rho, fck_MPa, sigma_cp_MPa=0.0, gamma_c=gamma_c, av_over_2d=av_over_2d)
    vrd_c_kN = vrd_c.v_rd_c_MPa * perimetro.u_mm * d_mm / 1000.0
    return PunzonamentoPalo(
        u_mm=perimetro.u_mm, a_mm=a_mm, ved_kN=n_max_pila_kN, vrd_c_kN=vrd_c_kN,
        utilizzo=n_max_pila_kN / vrd_c_kN, verificato=n_max_pila_kN <= vrd_c_kN,
    )

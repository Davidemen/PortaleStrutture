"""Punching checks (EC2 §6.4) for the pile cap — split out of `taglio_punzonamento.py` to keep that
module under the 150-line budget (`docs/BUILD_CONTRACT.md`, rule 12).

Code-review fixes (docs review, not in the architecture bug list; all gated on `legacy_compat=False`
so the sheet reproduction is untouched):
- EC2 eq. 6.5's companion crushing check `VEd <= 0.5*b*d*ν*fcd` at the column/pile face is now
  computed and enters `verificato` (see `taglio_punzonamento.taglio`).
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
from strutture.shared.report import CalcError

from .models_taglio import Punzonamento, PunzonamentoPalo

PUNCHING_COEFFICIENT_COLUMN_FACE = 0.5  # sheet's own coefficient in front of nu*fcd at u0 (legacy_compat=True only).
BETA_ECCENTRICITY_COEFFICIENT = 1.8  # EC2 eq. 6.39, simplified interior-column approximation.


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
        else 2.0 * d_mm / a_mm  # EC2 eq. 6.50: 2d/a >= 1 (a perimeter closer than 2d INCREASES v_Rd,c); the
        # inverted a/(2d) understated V_Rd,c,palo ~10x on the example and made pile punching look governing
    )
    vrd_c = v_rd_c(k_eff, rho, fck_MPa, sigma_cp_MPa=0.0, gamma_c=gamma_c, av_over_2d=av_over_2d)
    vrd_c_kN = vrd_c.v_rd_c_MPa * perimetro.u_mm * d_mm / 1000.0
    return PunzonamentoPalo(
        u_mm=perimetro.u_mm, a_mm=a_mm, ved_kN=n_max_pila_kN, vrd_c_kN=vrd_c_kN,
        utilizzo=n_max_pila_kN / vrd_c_kN, verificato=n_max_pila_kN <= vrd_c_kN,
    )

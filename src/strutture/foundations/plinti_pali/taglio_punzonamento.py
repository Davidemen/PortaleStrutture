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

Punching checks (`punzonamento_colonna`, `punzonamento_palo`, re-exported here for the tool's public
API) live in `punzonamento.py` — see that module's docstring for the corresponding fixes."""
from strutture.shared.divergences import legacy
from strutture.shared.ec2_shear import k_size, v_rd_c, v_rd_max
from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.materials.concrete import ALPHA_CC
from strutture.shared.numeric import clamp
from strutture.shared.report import CalcError

from .models_taglio import Taglio
from .punzonamento import punzonamento_colonna, punzonamento_palo  # re-exported, see module docstring

__all__ = ["punzonamento_colonna", "punzonamento_palo", "taglio"]

MARGIN_EFFECTIVE_DEPTH_FACTOR = 2.0  # sheet's `d = H - cover - 2*øl` (Tool4's own, coarser than Tool2's 1.5*ø).
STRIP_WIDTH_MM = 1000.0  # the 1m design strip `flessione.py` computed `as_prov_mm2` for.
VED_MAX_COEFFICIENT = 0.5  # sheet-adjacent coefficient for the companion crushing check (legacy_compat=True only).
AV_MIN_FACTOR = 0.5  # EC2 §6.2.2(6): "for av < 0.5d the value av = 0.5d should be used".
AV_MAX_FACTOR = 2.0  # beyond av=2d the reduction no longer applies (beta capped at 1.0).


def _taglio_ridotto(
    nsd_kN: float, d_mm: float, ax_mm: float, av_mm: float, as_prov_x_mm2: float, fck_MPa: float, gamma_c: float,
    *, legacy_compat: bool,
) -> tuple[float, float, float, float, float, float]:
    """(ved_kN, ved_ridotto_kN, k, rho, vrd_c_MPa, vrd_c_kN): beam shear at the reduced distance `av`
    from the pile face, EC2 §6.2.2(6)."""
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
    return ved_kN, ved_ridotto_kN, k, rho, vrd_c.v_rd_c_MPa, vrd_c_kN


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
    ved_kN, ved_ridotto_kN, k, rho, vrd_c_MPa, vrd_c_kN = _taglio_ridotto(
        nsd_kN, d_mm, ax_mm, av_mm, as_prov_x_mm2, fck_MPa, gamma_c, legacy_compat=legacy_compat,
    )
    # Same coefficiente-vrd-max-taglio-punzonamento choice as punzonamento_colonna: the sheet's
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
        d_mm=d_mm, ved_kN=ved_kN, ved_ridotto_kN=ved_ridotto_kN, k=k, rho=rho, vrd_c_MPa=vrd_c_MPa,
        vrd_c_kN=vrd_c_kN, ved_max_kN=ved_max_kN, utilizzo=ved_ridotto_kN / vrd_c_kN, verificato=verificato,
    )

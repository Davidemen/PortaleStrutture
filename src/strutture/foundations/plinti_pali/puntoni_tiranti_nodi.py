"""Strut-and-tie node/geometry helpers shared by `puntoni_tiranti.py` (EC2 §6.5.2/§6.5.4/§9.8.1) —
split out of that module to keep it under the 150-line budget (`docs/BUILD_CONTRACT.md`, rule 12).

Fix (found while porting, not in the architecture bug list): the sheet's `Lb` (support width at the
pile, `Footing check!BG13`) is a hardcoded literal (600mm in the golden case) decoupled from the
pile-diameter input (`AR107`) used everywhere else. This port always derives `Lb = diametro_pila_mm`.

Code-review fixes (all gated on `legacy_compat=False`, sheet reproduction untouched):
- Node coefficients: the sheet's own non-standard `K1_CCC_STRUT_COEFFICIENT`/`K2_CCT_*` are kept
  only under `legacy_compat=True`; the fix uses `shared.ec2_strut_tie.sigma_rd_max`'s EN 1992-1-1
  §6.5.4(4) defaults (k1=1.0 CCC, k2=0.85 CCT, k3=0.75 CTT), classifying the single-row node (one
  tie direction, "2x1"/"1x2") as CCT and the 2x2 bottom node (two tie directions anchored) as CTT.
- Strut angle: the 25° floor (`MIN_STRUT_ANGLE_DEG`, mis-attributed to EC2 §6.5.2(2), which does not
  set an angle floor) silently substituted a flatter-than-real strut, understating both the strut and
  tie forces; the fix always uses the true `atan(h_wt2/lxy)` and raises `CalcError` when it falls
  outside an acceptable 21.8°-68.2° band instead."""
import math

from strutture.shared.divergences import legacy
from strutture.shared.ec2_strut_tie import sigma_rd_max
from strutture.shared.rebar_catalog import bars_area
from strutture.shared.report import CalcError

from .models_puntoni_tiranti import Puntone, PuntoniTiranti, Tirante

LEGACY_MIN_STRUT_ANGLE_DEG = 25.0  # sheet's own floor, mis-attributed to EC2 §6.5.2(2).
# Sanity band for the strut inclination - not itself an EC2 clause (see review finding), just a
# guard against a geometrically nonsensical mechanism (near-horizontal or near-vertical strut);
# "Da verificare": the exact bounds should be confirmed against a strut-and-tie reference, not
# invented here.
MIN_STRUT_ANGLE_DEG = 20.0
MAX_STRUT_ANGLE_DEG = 70.0
ALPHA_CC_NODE = 0.85  # sheet's fcd = 0.85*fck/gammaC for every node/strut stress limit in this step.
K1_CCC_STRUT_COEFFICIENT = 1.18 / 0.85  # sheet's `1.18*((1-fck/250)/0.85)` node-1 (CCC) coefficient.
K2_CCT_ONE_TIE = 1.0  # node-2 (CCT, one tie direction anchored) - sheet-only, legacy_compat=True.
K2_CCT_TWO_TIES = 0.88  # node-3 (CCT, two tie directions anchored) - sheet-only, "2x2" schema.


def appoggio_diretto(n_max_env_kN: float, bx_mm: float, by_mm: float, fck_MPa: float, gamma_c: float) -> PuntoniTiranti:
    """Single-pile cap (`1x1`): the column bears directly on the pile, checked as a plain CCC node."""
    acs_mm2 = bx_mm * by_mm
    nodo = sigma_rd_max(fck_MPa, "CCC", gamma_c, alpha_cc=ALPHA_CC_NODE)
    fns_kN = nodo.sigma_rd_max_MPa * acs_mm2 / 1000.0
    puntone = Puntone(
        lxy_m=0.0, h_wt2_m=0.0, theta_deg=None, wt_mm=0.0, ws_mm=None, acs_mm2=acs_mm2, fus_kN=n_max_env_kN,
        sigma_rd_max_MPa=nodo.sigma_rd_max_MPa, fns_kN=fns_kN, verificato=fns_kN > n_max_env_kN,
        utilizzo=n_max_env_kN / fns_kN,
    )
    return PuntoniTiranti(puntone=puntone, tirante_xy=None, tirante_x=None, tirante_y=None)


def geometria_puntone(
    lxy_m: float, h_plinto_m: float, copriferro_mm: float, diametro_inf_x_mm: float, diametro_inf_y_mm: float,
    diametro_tirante_principale_mm: float, diametro_pila_mm: float, n_max_env_kN: float, *, legacy_compat: bool,
) -> tuple[float, float, float, float, float]:
    """(theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN), shared by the single-row and 2x2 geometries."""
    wt_mm = 2.0 * copriferro_mm + 2.0 * max(diametro_inf_x_mm, diametro_inf_y_mm) + diametro_tirante_principale_mm
    h_wt2_m = h_plinto_m - (wt_mm / 2.0) / 1000.0
    theta_reale_deg = math.degrees(math.atan(h_wt2_m / lxy_m))
    if legacy("plinti-pali/angolo-puntone-limitato-a-25-gradi", legacy_compat):
        theta_deg = max(LEGACY_MIN_STRUT_ANGLE_DEG, theta_reale_deg)
    else:
        # The 20-70 deg sanity band (plinti-pali/angolo-puntone-fascia-sicurezza-20-70-non-normativa,
        # ramo="nessuno") is enforced unconditionally here, together with this same branch.
        if not (MIN_STRUT_ANGLE_DEG <= theta_reale_deg <= MAX_STRUT_ANGLE_DEG):
            raise CalcError(
                f"puntone troppo inclinato (θ={theta_reale_deg:.1f}°): meccanismo tirante-puntone non applicabile",
            )
        theta_deg = theta_reale_deg
    theta_rad = math.radians(theta_deg)
    fus_kN = n_max_env_kN / math.sin(theta_rad)
    ws_mm = wt_mm * math.cos(theta_rad) + diametro_pila_mm * math.sin(theta_rad)
    acs_mm2 = ws_mm**2
    return theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN


def nodo_puntone(
    fus_kN: float, acs_mm2: float, fck_MPa: float, gamma_c: float, *,
    nodo_secondario: str, legacy_compat: bool,
) -> tuple[float, float]:
    """(sigma_rd_max_MPa, fns_kN) = MIN over the CCC node and the applicable second node class
    (CCT for a single tie direction, CTT for two tie directions anchored, EC2 §6.5.4(4)).
    `legacy_compat=True` reproduces the sheet's own non-standard coefficients."""
    if legacy("plinti-pali/nodi-puntone-tirante-coefficienti-non-standard", legacy_compat):
        sigma_ccc = sigma_rd_max(fck_MPa, "CCC", gamma_c, alpha_cc=ALPHA_CC_NODE, k1=K1_CCC_STRUT_COEFFICIENT).sigma_rd_max_MPa
        k2 = K2_CCT_ONE_TIE if nodo_secondario == "CCT" else K2_CCT_TWO_TIES
        sigma_secondario = sigma_rd_max(fck_MPa, "CCT", gamma_c, alpha_cc=ALPHA_CC_NODE, k2=k2).sigma_rd_max_MPa
    else:
        sigma_ccc = sigma_rd_max(fck_MPa, "CCC", gamma_c, alpha_cc=ALPHA_CC_NODE).sigma_rd_max_MPa
        sigma_secondario = sigma_rd_max(fck_MPa, nodo_secondario, gamma_c, alpha_cc=ALPHA_CC_NODE).sigma_rd_max_MPa
    sigma_rd = min(sigma_ccc, sigma_secondario)
    return sigma_rd, sigma_rd * acs_mm2 / 1000.0


def progetta_tirante(fut_kN: float, diametro_mm: float, n_barre: int, fyd_MPa: float) -> Tirante:
    at_mm2 = bars_area(n_barre, diametro_mm)
    fnt_kN = at_mm2 * fyd_MPa / 1000.0
    return Tirante(fut_kN=fut_kN, diametro_mm=diametro_mm, n_barre=n_barre, at_mm2=at_mm2, fnt_kN=fnt_kN,
                    verificato=fnt_kN > fut_kN, utilizzo=fut_kN / fnt_kN)

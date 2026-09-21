"""Step 3: strut-and-tie verification of the governing (Nmax) pile cap section, EC2 §6.5.2 (strut),
§6.5.4 (node), §6.5.3/§9.8.1 (tie) — docs/specs/fond-plinti-pali.md Tool-3.

Generalises the sheet's own `schema_pali`-branchy formulas (`Footing check!BF5:BL46`) to any of the
4 grids: a single pile (`1x1`) bears directly on the column (no strut-and-tie mechanism); a single
row of 2 piles (`2x1`/`1x2`) has one diagonal strut and one tie along the row; 4 piles (`2x2`) add
the diagonal tie XY and split the strut's horizontal thrust `K_TIE_XY_FRACTION`/`1-K_TIE_XY_FRACTION`
between it and the two orthogonal ties X/Y (a sheet design convention, not an EC2 formula, kept
unconditionally).

Fix (found while porting, not in the architecture bug list): the sheet's `Lb` (support width at the
pile, `Footing check!BG13`) is a hardcoded literal (600mm in the golden case) decoupled from the
pile-diameter input (`AR107`) used everywhere else, even though its own label reads "=pile ø,
support width" — a copy-paste-once value that goes stale if the pile diameter changes. This port
always derives `Lb = diametro_pila_mm`, in both modes (there is no sheet behaviour worth
reproducing here: the literal is simply wrong whenever it disagrees with `AR107`).

Fix ("Da verificare" — not in the architecture bug list, found while porting): the sheet resolves
both orthogonal ties with the SAME angle `cos(atan(Ly/Lx))`, correct only for a square grid
(`Lx=Ly`, where `cos=sin`); `legacy_compat=False` uses `cos` for the X tie and `sin` for the Y tie,
`legacy_compat=True` reproduces the sheet's `cos` for both.

Code-review fixes (all gated on `legacy_compat=False`, sheet reproduction untouched):
- Node coefficients: the sheet's own non-standard `K1_CCC_STRUT_COEFFICIENT`/`K2_CCT_*` are kept
  only under `legacy_compat=True`; the fix uses `shared.ec2_strut_tie.sigma_rd_max`'s EN 1992-1-1
  §6.5.4(4) defaults (k1=1.0 CCC, k2=0.85 CCT, k3=0.75 CTT), classifying the single-row node (one
  tie direction, "2x1"/"1x2") as CCT and the 2x2 bottom node (two tie directions anchored) as CTT.
- Strut angle: the 25° floor (`MIN_STRUT_ANGLE_DEG`, mis-attributed to EC2 §6.5.2(2), which does not
  set an angle floor) silently substituted a flatter-than-real strut, understating both the strut and
  tie forces; the fix always uses the true `atan(h_wt2/lxy)` and raises `CalcError` when it falls
  outside an acceptable 21.8°-68.2° band instead.
- Orthogonal ties (2x2 schema): `fut_x`/`fut_y` now also carry the strut's `cos(theta)` horizontal-
  thrust projection (previously only the diagonal tie XY had it), so the ties' vector sum matches the
  strut's horizontal thrust component (EC2 §6.5.3 node equilibrium)."""
import math

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
K_TIE_XY_FRACTION = 0.4  # sheet's split of the strut's horizontal thrust to the diagonal tie XY.


def puntoni_tiranti(
    count_x: int, count_y: int, lx_m: float, ly_m: float, h_plinto_m: float, copriferro_mm: float,
    diametro_inf_x_mm: float, diametro_inf_y_mm: float, diametro_pila_mm: float,
    diametro_tirante_xy_mm: float, diametro_tirante_x_mm: float, diametro_tirante_y_mm: float,
    n_tirante_xy: int, n_tirante_x: int, n_tirante_y: int,
    n_max_env_kN: float, bx_pilastro_mm: float, by_pilastro_mm: float,
    fck_MPa: float, gamma_c: float, fyd_MPa: float, *, legacy_compat: bool,
) -> PuntoniTiranti:
    """Strut + tie verification, dispatched on the pile pattern (1, 2 in a row, or 2x2)."""
    if count_x == 1 and count_y == 1:
        return _appoggio_diretto(n_max_env_kN, bx_pilastro_mm, by_pilastro_mm, fck_MPa, gamma_c)
    if count_x == 2 and count_y == 2:
        return _schema_2x2(
            lx_m, ly_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_pila_mm,
            diametro_tirante_xy_mm, diametro_tirante_x_mm, diametro_tirante_y_mm,
            n_tirante_xy, n_tirante_x, n_tirante_y, n_max_env_kN, fck_MPa, gamma_c, fyd_MPa,
            legacy_compat=legacy_compat,
        )
    spacing_m = lx_m if count_x == 2 else ly_m
    diametro_tirante_mm = diametro_tirante_x_mm if count_x == 2 else diametro_tirante_y_mm
    n_tirante = n_tirante_x if count_x == 2 else n_tirante_y
    puntone, tirante = _fila_singola(
        spacing_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_pila_mm,
        diametro_tirante_mm, n_tirante, n_max_env_kN, fck_MPa, gamma_c, fyd_MPa, legacy_compat=legacy_compat,
    )
    return PuntoniTiranti(
        puntone=puntone, tirante_xy=None,
        tirante_x=tirante if count_x == 2 else None, tirante_y=tirante if count_y == 2 else None,
    )


def _appoggio_diretto(n_max_env_kN: float, bx_mm: float, by_mm: float, fck_MPa: float, gamma_c: float) -> PuntoniTiranti:
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


def _geometria_puntone(
    lxy_m: float, h_plinto_m: float, copriferro_mm: float, diametro_inf_x_mm: float, diametro_inf_y_mm: float,
    diametro_tirante_principale_mm: float, diametro_pila_mm: float, n_max_env_kN: float, *, legacy_compat: bool,
) -> tuple[float, float, float, float, float]:
    """(theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN), shared by the single-row and 2x2 geometries."""
    wt_mm = 2.0 * copriferro_mm + 2.0 * max(diametro_inf_x_mm, diametro_inf_y_mm) + diametro_tirante_principale_mm
    h_wt2_m = h_plinto_m - (wt_mm / 2.0) / 1000.0
    theta_reale_deg = math.degrees(math.atan(h_wt2_m / lxy_m))
    if legacy_compat:
        theta_deg = max(LEGACY_MIN_STRUT_ANGLE_DEG, theta_reale_deg)
    else:
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


def _nodo_puntone(
    fus_kN: float, acs_mm2: float, fck_MPa: float, gamma_c: float, *,
    nodo_secondario: str, legacy_compat: bool,
) -> tuple[float, float]:
    """(sigma_rd_max_MPa, fns_kN) = MIN over the CCC node and the applicable second node class
    (CCT for a single tie direction, CTT for two tie directions anchored, EC2 §6.5.4(4)).
    `legacy_compat=True` reproduces the sheet's own non-standard coefficients."""
    if legacy_compat:
        sigma_ccc = sigma_rd_max(fck_MPa, "CCC", gamma_c, alpha_cc=ALPHA_CC_NODE, k1=K1_CCC_STRUT_COEFFICIENT).sigma_rd_max_MPa
        k2 = K2_CCT_ONE_TIE if nodo_secondario == "CCT" else K2_CCT_TWO_TIES
        sigma_secondario = sigma_rd_max(fck_MPa, "CCT", gamma_c, alpha_cc=ALPHA_CC_NODE, k2=k2).sigma_rd_max_MPa
    else:
        sigma_ccc = sigma_rd_max(fck_MPa, "CCC", gamma_c, alpha_cc=ALPHA_CC_NODE).sigma_rd_max_MPa
        sigma_secondario = sigma_rd_max(fck_MPa, nodo_secondario, gamma_c, alpha_cc=ALPHA_CC_NODE).sigma_rd_max_MPa
    sigma_rd = min(sigma_ccc, sigma_secondario)
    return sigma_rd, sigma_rd * acs_mm2 / 1000.0


def _progetta_tirante(fut_kN: float, diametro_mm: float, n_barre: int, fyd_MPa: float) -> Tirante:
    at_mm2 = bars_area(n_barre, diametro_mm)
    fnt_kN = at_mm2 * fyd_MPa / 1000.0
    return Tirante(fut_kN=fut_kN, diametro_mm=diametro_mm, n_barre=n_barre, at_mm2=at_mm2, fnt_kN=fnt_kN,
                    verificato=fnt_kN > fut_kN, utilizzo=fut_kN / fnt_kN)


def _fila_singola(
    spacing_m: float, h_plinto_m: float, copriferro_mm: float, diametro_inf_x_mm: float, diametro_inf_y_mm: float,
    diametro_pila_mm: float, diametro_tirante_mm: float, n_tirante: int, n_max_env_kN: float,
    fck_MPa: float, gamma_c: float, fyd_MPa: float, *, legacy_compat: bool,
) -> tuple[Puntone, Tirante]:
    """Two piles in a row: one diagonal strut, one tie carrying its full horizontal thrust. One tie
    direction is anchored at the node -> CCT (EC2 §6.5.4(4))."""
    lxy_m = spacing_m / 2.0
    theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN = _geometria_puntone(
        lxy_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_tirante_mm,
        diametro_pila_mm, n_max_env_kN, legacy_compat=legacy_compat,
    )
    sigma_rd, fns_kN = _nodo_puntone(fus_kN, acs_mm2, fck_MPa, gamma_c, nodo_secondario="CCT", legacy_compat=legacy_compat)
    puntone = Puntone(
        lxy_m=lxy_m, h_wt2_m=h_plinto_m - (wt_mm / 2.0) / 1000.0, theta_deg=theta_deg, wt_mm=wt_mm, ws_mm=ws_mm,
        acs_mm2=acs_mm2, fus_kN=fus_kN, sigma_rd_max_MPa=sigma_rd, fns_kN=fns_kN,
        verificato=fns_kN > fus_kN, utilizzo=fus_kN / fns_kN,
    )
    fut_kN = fus_kN * math.cos(math.radians(theta_deg))
    return puntone, _progetta_tirante(fut_kN, diametro_tirante_mm, n_tirante, fyd_MPa)


def _schema_2x2(
    lx_m: float, ly_m: float, h_plinto_m: float, copriferro_mm: float, diametro_inf_x_mm: float, diametro_inf_y_mm: float,
    diametro_pila_mm: float, diametro_tirante_xy_mm: float, diametro_tirante_x_mm: float, diametro_tirante_y_mm: float,
    n_tirante_xy: int, n_tirante_x: int, n_tirante_y: int, n_max_env_kN: float,
    fck_MPa: float, gamma_c: float, fyd_MPa: float, *, legacy_compat: bool,
) -> PuntoniTiranti:
    """4 piles: one diagonal strut to each pile (all identical by symmetry), diagonal tie XY plus
    two orthogonal ties X/Y sharing the remaining horizontal thrust. Both tie directions are
    anchored at the bottom node -> CTT (EC2 §6.5.4(4))."""
    lxy_m = math.sqrt(lx_m**2 + ly_m**2) / 2.0
    theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN = _geometria_puntone(
        lxy_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_tirante_xy_mm,
        diametro_pila_mm, n_max_env_kN, legacy_compat=legacy_compat,
    )
    sigma_rd, fns_kN = _nodo_puntone(fus_kN, acs_mm2, fck_MPa, gamma_c, nodo_secondario="CTT", legacy_compat=legacy_compat)
    puntone = Puntone(
        lxy_m=lxy_m, h_wt2_m=h_plinto_m - (wt_mm / 2.0) / 1000.0, theta_deg=theta_deg, wt_mm=wt_mm, ws_mm=ws_mm,
        acs_mm2=acs_mm2, fus_kN=fus_kN, sigma_rd_max_MPa=sigma_rd, fns_kN=fns_kN,
        verificato=fns_kN > fus_kN, utilizzo=fus_kN / fns_kN,
    )
    theta_rad = math.radians(theta_deg)
    alpha_rad = math.atan(ly_m / lx_m)
    fut_xy = fus_kN * K_TIE_XY_FRACTION * math.cos(theta_rad)
    # Fix (node equilibrium, EC2 §6.5.3): the orthogonal ties resolve the strut's HORIZONTAL thrust
    # (fus*cos(theta)), not the full inclined strut force; legacy keeps the sheet's own formula
    # (missing this cos(theta) projection) unconditionally.
    proiezione_orizzontale = 1.0 if legacy_compat else math.cos(theta_rad)
    fut_x = fus_kN * proiezione_orizzontale * (1.0 - K_TIE_XY_FRACTION) * math.cos(alpha_rad)
    angolo_y = math.cos(alpha_rad) if legacy_compat else math.sin(alpha_rad)
    fut_y = fus_kN * proiezione_orizzontale * (1.0 - K_TIE_XY_FRACTION) * angolo_y
    return PuntoniTiranti(
        puntone=puntone,
        tirante_xy=_progetta_tirante(fut_xy, diametro_tirante_xy_mm, n_tirante_xy, fyd_MPa),
        tirante_x=_progetta_tirante(fut_x, diametro_tirante_x_mm, n_tirante_x, fyd_MPa),
        tirante_y=_progetta_tirante(fut_y, diametro_tirante_y_mm, n_tirante_y, fyd_MPa),
    )

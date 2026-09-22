"""Step 3: strut-and-tie verification of the governing (Nmax) pile cap section, EC2 §6.5.2 (strut),
§6.5.4 (node), §6.5.3/§9.8.1 (tie) — docs/specs/fond-plinti-pali.md Tool-3.

Generalises the sheet's own `schema_pali`-branchy formulas (`Footing check!BF5:BL46`) to any of the
4 grids: a single pile (`1x1`) bears directly on the column (no strut-and-tie mechanism); a single
row of 2 piles (`2x1`/`1x2`) has one diagonal strut and one tie along the row; 4 piles (`2x2`) add
the diagonal tie XY and split the strut's horizontal thrust `K_TIE_XY_FRACTION`/`1-K_TIE_XY_FRACTION`
between it and the two orthogonal ties X/Y (a sheet design convention, not an EC2 formula, kept
unconditionally).

Node/geometry helpers (single-row and 2x2 strut geometry, node stress limits, tie sizing) live in
`puntoni_tiranti_nodi.py` (see that module's docstring for the corresponding fixes).

Fix ("Da verificare" — not in the architecture bug list, found while porting): the sheet resolves
both orthogonal ties with the SAME angle `cos(atan(Ly/Lx))`, correct only for a square grid
(`Lx=Ly`, where `cos=sin`); `legacy_compat=False` uses `cos` for the X tie and `sin` for the Y tie,
`legacy_compat=True` reproduces the sheet's `cos` for both.

Code-review fix (gated on `legacy_compat=False`, sheet reproduction untouched):
- Orthogonal ties (2x2 schema): `fut_x`/`fut_y` now also carry the strut's `cos(theta)` horizontal-
  thrust projection (previously only the diagonal tie XY had it), so the ties' vector sum matches the
  strut's horizontal thrust component (EC2 §6.5.3 node equilibrium)."""
import math

from strutture.shared.divergences import legacy

from .models_puntoni_tiranti import Puntone, PuntoniTiranti, Tirante
from .puntoni_tiranti_nodi import appoggio_diretto, geometria_puntone, nodo_puntone, progetta_tirante

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
        return appoggio_diretto(n_max_env_kN, bx_pilastro_mm, by_pilastro_mm, fck_MPa, gamma_c)
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


def _fila_singola(
    spacing_m: float, h_plinto_m: float, copriferro_mm: float, diametro_inf_x_mm: float, diametro_inf_y_mm: float,
    diametro_pila_mm: float, diametro_tirante_mm: float, n_tirante: int, n_max_env_kN: float,
    fck_MPa: float, gamma_c: float, fyd_MPa: float, *, legacy_compat: bool,
) -> tuple[Puntone, Tirante]:
    """Two piles in a row: one diagonal strut, one tie carrying its full horizontal thrust. One tie
    direction is anchored at the node -> CCT (EC2 §6.5.4(4))."""
    lxy_m = spacing_m / 2.0
    theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN = geometria_puntone(
        lxy_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_tirante_mm,
        diametro_pila_mm, n_max_env_kN, legacy_compat=legacy_compat,
    )
    sigma_rd, fns_kN = nodo_puntone(fus_kN, acs_mm2, fck_MPa, gamma_c, nodo_secondario="CCT", legacy_compat=legacy_compat)
    puntone = Puntone(
        lxy_m=lxy_m, h_wt2_m=h_plinto_m - (wt_mm / 2.0) / 1000.0, theta_deg=theta_deg, wt_mm=wt_mm, ws_mm=ws_mm,
        acs_mm2=acs_mm2, fus_kN=fus_kN, sigma_rd_max_MPa=sigma_rd, fns_kN=fns_kN,
        verificato=fns_kN > fus_kN, utilizzo=fus_kN / fns_kN,
    )
    fut_kN = fus_kN * math.cos(math.radians(theta_deg))
    return puntone, progetta_tirante(fut_kN, diametro_tirante_mm, n_tirante, fyd_MPa)


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
    theta_deg, wt_mm, ws_mm, acs_mm2, fus_kN = geometria_puntone(
        lxy_m, h_plinto_m, copriferro_mm, diametro_inf_x_mm, diametro_inf_y_mm, diametro_tirante_xy_mm,
        diametro_pila_mm, n_max_env_kN, legacy_compat=legacy_compat,
    )
    sigma_rd, fns_kN = nodo_puntone(fus_kN, acs_mm2, fck_MPa, gamma_c, nodo_secondario="CTT", legacy_compat=legacy_compat)
    puntone = Puntone(
        lxy_m=lxy_m, h_wt2_m=h_plinto_m - (wt_mm / 2.0) / 1000.0, theta_deg=theta_deg, wt_mm=wt_mm, ws_mm=ws_mm,
        acs_mm2=acs_mm2, fus_kN=fus_kN, sigma_rd_max_MPa=sigma_rd, fns_kN=fns_kN,
        verificato=fns_kN > fus_kN, utilizzo=fus_kN / fns_kN,
    )
    tiranti = _tiranti_2x2(
        lx_m, ly_m, fus_kN, theta_deg, diametro_tirante_xy_mm, diametro_tirante_x_mm, diametro_tirante_y_mm,
        n_tirante_xy, n_tirante_x, n_tirante_y, fyd_MPa, legacy_compat=legacy_compat,
    )
    return PuntoniTiranti(puntone=puntone, tirante_xy=tiranti[0], tirante_x=tiranti[1], tirante_y=tiranti[2])


def _tiranti_2x2(
    lx_m: float, ly_m: float, fus_kN: float, theta_deg: float,
    diametro_tirante_xy_mm: float, diametro_tirante_x_mm: float, diametro_tirante_y_mm: float,
    n_tirante_xy: int, n_tirante_x: int, n_tirante_y: int, fyd_MPa: float, *, legacy_compat: bool,
) -> tuple[Tirante, Tirante, Tirante]:
    """Diagonal tie XY plus the two orthogonal ties X/Y, split from the strut's horizontal thrust."""
    theta_rad = math.radians(theta_deg)
    alpha_rad = math.atan(ly_m / lx_m)
    fut_xy = fus_kN * K_TIE_XY_FRACTION * math.cos(theta_rad)
    # Fix (node equilibrium, EC2 §6.5.3): the orthogonal ties resolve the strut's HORIZONTAL thrust
    # (fus*cos(theta)), not the full inclined strut force; legacy keeps the sheet's own formula
    # (missing this cos(theta) projection) unconditionally.
    proiezione_orizzontale = (
        1.0 if legacy("plinti-pali/tiranti-2x2-senza-proiezione-coseno", legacy_compat) else math.cos(theta_rad)
    )
    fut_x = fus_kN * proiezione_orizzontale * (1.0 - K_TIE_XY_FRACTION) * math.cos(alpha_rad)
    angolo_y = (
        math.cos(alpha_rad)
        if legacy("plinti-pali/tiranti-ortogonali-stesso-angolo-griglia-non-quadrata", legacy_compat)
        else math.sin(alpha_rad)
    )
    fut_y = fus_kN * proiezione_orizzontale * (1.0 - K_TIE_XY_FRACTION) * angolo_y
    return (
        progetta_tirante(fut_xy, diametro_tirante_xy_mm, n_tirante_xy, fyd_MPa),
        progetta_tirante(fut_x, diametro_tirante_x_mm, n_tirante_x, fyd_MPa),
        progetta_tirante(fut_y, diametro_tirante_y_mm, n_tirante_y, fyd_MPa),
    )

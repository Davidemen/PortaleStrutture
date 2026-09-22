"""Section resistance quantities (column-check!Q39-Q41), split out of `sezione.py` (regola dura 12).

Re-exported by `sezione.py`, the package's entry point for section-derived quantities.
"""
from strutture.shared.divergences import legacy
from strutture.shared.report import CalcError
from strutture.shared.units import n_to_kn, nmm_to_knm


def momento_plastico_resistente_kNm(
    classe: int, wel_mm3: float, wpl_mm3: float, fy_MPa: float
) -> float:
    """column-check!Q39/Q40 — Wpl*fy for class 1/2, Wel*fy for class 3/4 (fy = fyd or fyk, per caller)."""
    modulo = wel_mm3 if classe >= 3 else wpl_mm3
    return nmm_to_knm(modulo * fy_MPa)


def npl_kN(area_mm2: float, fy_MPa: float) -> float:
    """column-check!Q41 — Npl = A*fy (fy = fyd or fyk, per caller)."""
    return n_to_kn(area_mm2 * fy_MPa)


def verifica_classe_supportata(classe_num: int, *, legacy_compat: bool) -> None:
    """Class 4 has no effective-width implementation (§4.4) in this module — see `sezione.py` docstring."""
    if classe_num == 4 and not legacy("acciaio-colonna-ec3/classe-4-non-implementata", legacy_compat):
        raise CalcError(
            "Sezione di classe 4: nessun calcolo di area/moduli efficaci (EN1993-1-5 §4.4) "
            "implementato; la resistenza sulla sezione lorda non è conservativa."
        )


def campi_resistenza(
    *, classe_num: int, area_mm2: float, wel_y_mm3: float, wpl_y_mm3: float, wel_z_mm3: float, wpl_z_mm3: float,
    fyd_MPa: float, fyk_MPa: float,
) -> dict[str, float]:
    """Npl/Mpl di progetto (Q39-Q41) e caratteristici (per eq. 6.61/6.62, §6.3.3)."""
    return {
        "npl_kN": npl_kN(area_mm2, fyd_MPa),
        "mpl_y_kNm": momento_plastico_resistente_kNm(classe_num, wel_y_mm3, wpl_y_mm3, fyd_MPa),
        "mpl_z_kNm": momento_plastico_resistente_kNm(classe_num, wel_z_mm3, wpl_z_mm3, fyd_MPa),
        "npl_rk_kN": npl_kN(area_mm2, fyk_MPa),
        "mpl_y_rk_kNm": momento_plastico_resistente_kNm(classe_num, wel_y_mm3, wpl_y_mm3, fyk_MPa),
        "mpl_z_rk_kNm": momento_plastico_resistente_kNm(classe_num, wel_z_mm3, wpl_z_mm3, fyk_MPa),
    }

"""Step: section geometry (Ac, As, ρs) and minimum eccentricity (H18:H23 / rows 9-11, 18-20)."""
from strutture.shared.rebar_catalog import bars_area
from strutture.shared.section_geometry import circle, equivalent_square, rect
from strutture.shared.units import mm_to_m

MIN_ECCENTRICITY_MM = 20.0  # H18 floor
MIN_ECCENTRICITY_RATIO = 0.05  # H18 = max(20, 0.05*dimensione_max)


def sezione_rettangolare(l1_mm: float, l2_mm: float, n_ferri: int, diametro_ferri_mm: float) -> tuple[float, float, float]:
    """H21 (Ac), H22 (As), H23 (ρs)."""
    ac_mm2 = rect(l1_mm, l2_mm).area_mm2
    as_mm2 = bars_area(n_ferri, diametro_ferri_mm)
    return ac_mm2, as_mm2, as_mm2 / ac_mm2


def sezione_circolare(d_mm: float, n_ferri: int, diametro_ferri_mm: float) -> tuple[float, float, float, float]:
    """H21 (Ac), H22 (As), H23 (ρs), CX17 (lato del quadrato equivalente)."""
    ac_mm2 = circle(d_mm).area_mm2
    as_mm2 = bars_area(n_ferri, diametro_ferri_mm)
    return ac_mm2, as_mm2, as_mm2 / ac_mm2, equivalent_square(ac_mm2)


def eccentricita_minima(dimensione_max_mm: float, ned_kN: float, med_kNm: float) -> tuple[float, float, float]:
    """H18 (e_min), H19 (MEd,ecc), H20 (MEd di calcolo)."""
    e_min_mm = max(MIN_ECCENTRICITY_MM, MIN_ECCENTRICITY_RATIO * dimensione_max_mm)
    med_ecc_kNm = ned_kN * mm_to_m(e_min_mm)
    return e_min_mm, med_ecc_kNm, max(med_ecc_kNm, med_kNm)


def leva_interna(dimensione_mm: float, c_mm: float) -> float:
    """CX30: z = 0.9*(dimensione - copriferro)."""
    return 0.9 * (dimensione_mm - c_mm)

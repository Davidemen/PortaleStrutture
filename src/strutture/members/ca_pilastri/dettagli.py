"""Step: detailing checks, NTC2018 §7.4.6.2.2 / EC8 5.4.3.2.2, rows J60-J64 (rett.) / J67-J71 (circ.)."""
import math

LONG_BAR_MIN_DIAMETER_MM = 12.0  # J60/J67
LONG_BAR_MAX_SPACING_MM = 300.0  # J61/J68 — NTC2018 §4.1.6.1.2, limite NON sismico
LONG_BAR_MAX_SPACING_SEISMIC_MM = 250.0  # NTC2018 §7.4.6.2.2 CD"B": "per tutta la lunghezza del
# pilastro l'interasse tra le barre non deve essere superiore a 25 cm" — review finding (MEDIUM):
# the sheet's own summary row (and this tool's check) was labelled §7.4.6.2.2 but numerically
# reused the §4.1.6.1.2 non-seismic 300mm limit; legacy_compat=True keeps the sheet's own 300mm.
STIRRUP_MIN_DIAMETER_FIXED_MM = 6.0  # CX22
STIRRUP_MIN_DIAMETER_BAR_DIVISOR = 4.0  # CX23 = Ø_long/4
STIRRUP_SPACING_MAX_BAR_MULTIPLIER = 12.0  # CX20 = 12*Ø_long
STIRRUP_SPACING_MAX_FIXED_MM = 250.0  # CX21


def perimetro_circolare_mm(dimensione_mm: float, c_mm: float) -> float:
    """CX24 (sezione circolare): 2π·((D/2)-c) — corretta per il pilastro circolare; riusata (bug)
    sul foglio rettangolare, vedi `perimetro_rettangolare_mm` e docs/divergences/ca-pilastri.md."""
    return 2.0 * math.pi * (dimensione_mm / 2.0 - c_mm)


def perimetro_rettangolare_mm(l1_mm: float, l2_mm: float, c_mm: float) -> float:
    """Fix per la sezione rettangolare (architecture.md §6: "per-face perimeter spacing"): perimetro
    della gabbia di armatura (lati ridotti del copriferro), non l'approssimazione circolare."""
    return 2.0 * ((l1_mm - 2 * c_mm) + (l2_mm - 2 * c_mm))


def interasse_ferri_verticali_mm(perimetro_mm: float, n_ferri: int) -> float:
    """CX24 / n: interasse tra i ferri longitudinali."""
    return perimetro_mm / n_ferri


def diametro_staffe_minimo_mm(diametro_ferri_mm: float, *, legacy_compat: bool, combinatore: str = "auto") -> float:
    """CX22 (=6mm fisso), CX23 (=Ø_long/4). Il warning "in linea" del foglio NTC (K16) usa
    correttamente MAX (bisogna soddisfare entrambi i minimi, NTC2018 §7.4.6.2.2); la riga di
    sintesi NTC2008/NTC2018 (J63/J70) usa invece MIN — un'aggregazione non conservativa, corretta
    qui sotto `legacy_compat=False`. Il foglio EC2 usa già MAX in entrambe le modalità (nessuna
    divergenza sull'aggregatore, solo sulla cella di confronto — vedi `tool_*.py`): passare
    `combinatore="max"` per riprodurlo."""
    candidati = (STIRRUP_MIN_DIAMETER_FIXED_MM, diametro_ferri_mm / STIRRUP_MIN_DIAMETER_BAR_DIVISOR)
    if combinatore == "max":
        return max(candidati)
    return min(candidati) if legacy_compat else max(candidati)


def interasse_staffe_massimo_mm(
    diametro_ferri_mm: float, *,
    bar_multiplier: float = STIRRUP_SPACING_MAX_BAR_MULTIPLIER,
    fixed_mm: float = STIRRUP_SPACING_MAX_FIXED_MM,
    dimensione_min_mm: float | None = None,
) -> float:
    """CX20/CX21 → MIN(CX20,CX21) (NTC: 12·Ø/250mm). EC2 §9.5.3(3) changes the two constants to
    20·Ø/400mm and adds a 3rd candidate, the column's own smaller side (`dimensione_min_mm`)."""
    candidati = (bar_multiplier * diametro_ferri_mm, fixed_mm, *((dimensione_min_mm,) if dimensione_min_mm is not None else ()))
    return min(candidati)

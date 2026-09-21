"""Step: confined (critical) zone height and stirrup spacing, NTC2018 §7.4.6.2.2, rows Z24-Z25.

For the rectangular column, `altezza_critica_mm` must receive the LARGER section dimension
(NTC2018 §7.4.6.1.2: lcr = max(h_sez,max; lc/6; 450mm), whole-column-critical threshold lc/h < 3
with h the larger dimension) and `passo_massimo_confinato_mm` the SMALLER confined-core dimension
b0 (NTC2018 §7.4.6.2.2 CD"B": s <= min(b0/2; 175mm; 8*Ø_long)) — see `tool_rettangolare.py`, which
passes `max(l1_mm, l2_mm)` / `min(l1_mm, l2_mm)` respectively (review finding, HIGH). The circular
column has a single dimension so this distinction does not apply there."""

CONFINED_HEIGHT_SPAN_MULTIPLIER = 3.0  # Z24: soglia H < 3*dimensione
CONFINED_HEIGHT_FLOOR_MM = 450.0
CONFINED_HEIGHT_SPAN_DIVISOR = 6.0
CONFINED_SPACING_HALF_DIMENSION = 2.0  # CX45 = dimensione/2
CONFINED_SPACING_FIXED_MM = 175.0  # CX46
CONFINED_SPACING_LONG_BAR_MULTIPLIER = 8.0  # CX47 = 8*Ø_longitudinale


def altezza_critica_mm(h_mm: float, dimensione_mm: float) -> float:
    """Z24 (hcr)."""
    if h_mm < CONFINED_HEIGHT_SPAN_MULTIPLIER * dimensione_mm:
        return h_mm
    return max(dimensione_mm, h_mm / CONFINED_HEIGHT_SPAN_DIVISOR, CONFINED_HEIGHT_FLOOR_MM)


def passo_massimo_confinato_mm(dimensione_mm: float, diametro_ferri_mm: float) -> float:
    """Z25: MIN(CX45:CX47) — il candidato più restrittivo."""
    candidati = (
        dimensione_mm / CONFINED_SPACING_HALF_DIMENSION,
        CONFINED_SPACING_FIXED_MM,
        CONFINED_SPACING_LONG_BAR_MULTIPLIER * diametro_ferri_mm,
    )
    return min(candidati)

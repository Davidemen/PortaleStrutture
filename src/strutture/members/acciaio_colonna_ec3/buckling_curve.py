"""Buckling curve selection (EN1993-1-1 Tab. 6.1/6.2/6.3; column-check!BC17/BC25/Y25/Y26).

Known bug (docs/architecture.md §6, `acciaio Y25/Y26`): the sheet derives the flexural-buckling
imperfection factors alpha_yy/alpha_zz directly from `IF(processing="hot finished", ...)` hardcoded
pairs, bypassing the buckling-curve letter entirely — a duplicated, divergence-prone source of
truth. Fixed behaviour derives alpha_yy/alpha_zz from a genuine Tab. 6.2 curve-per-axis selection
(h/b and tf rules) through the single shared curve->alpha table (`tables.ALPHA_PER_CURVA`), the
same table already used (correctly) for the LTB curve BC17/BC25.

The LTB curve BC17 itself is not flagged as buggy and is reproduced identically in both modes: its
hot/cold + h/b<=2 rule matches EN1993-1-1 Tab. 6.3 (general case, LTB curve selection for rolled vs
welded I-sections) even though the sheet labels the dropdown "processing" (hot finished/cold
formed) rather than "rolled/welded" — see docs/divergences/acciaio-colonna-ec3.md (Da verificare)
for the residual uncertainty on that label mapping for "cold formed" open I/H sections.
"""
from .models import TipoLavorazione
from .tables import ALPHA_PER_CURVA, LIMITE_HB_TAB_6_2, LIMITE_TF_SOTTILE_MM, LIMITE_TF_SPESSA_MM


def curva_lt(h_mm: float, b_mm: float, lavorazione: TipoLavorazione) -> str:
    """column-check!BC17 — LTB buckling curve (Tab. 6.3-like), identical in both modes."""
    hot = lavorazione == "hot finished"
    snella = (h_mm / b_mm) <= 2.0
    if hot:
        return "b" if snella else "c"
    return "c" if snella else "d"


def alpha_lt(curva: str) -> float:
    """column-check!BC25 — alpha for the LTB curve letter."""
    return ALPHA_PER_CURVA[curva]


def curve_flessionali_tab_6_2(h_mm: float, b_mm: float, tf_mm: float) -> tuple[str, str]:
    """(curva_yy, curva_zz) per EN1993-1-1 Tab. 6.2, rolled I/H sections (fixed-mode only).

    Rows keyed on h/b and tf; no S460-specific a0 row (out of scope, grades here top out at S355).
    """
    h_su_b = h_mm / b_mm
    if h_su_b > LIMITE_HB_TAB_6_2:
        if tf_mm <= LIMITE_TF_SOTTILE_MM:
            return "a", "b"
        if tf_mm <= LIMITE_TF_SPESSA_MM:
            return "b", "c"
        return "d", "d"
    if tf_mm <= LIMITE_TF_SPESSA_MM:
        return "b", "c"
    return "d", "d"


def alpha_flessionali(
    h_mm: float,
    b_mm: float,
    tf_mm: float,
    lavorazione: TipoLavorazione,
    *,
    legacy_compat: bool,
) -> tuple[float, float, str, str]:
    """(alpha_yy, alpha_zz, curva_yy, curva_zz). Legacy reproduces column-check!Y25/Y26 exactly."""
    curva_yy, curva_zz = curve_flessionali_tab_6_2(h_mm, b_mm, tf_mm)
    if legacy_compat:
        hot = lavorazione == "hot finished"
        return (0.34 if hot else 0.21), (0.49 if hot else 0.34), curva_yy, curva_zz
    return ALPHA_PER_CURVA[curva_yy], ALPHA_PER_CURVA[curva_zz], curva_yy, curva_zz

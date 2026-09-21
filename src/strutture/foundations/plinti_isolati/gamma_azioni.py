"""Step 2: permanent-load factor gammaW applied to the footing self-weight (docs/specs/
fond-plinti-isolati.md Tool-1 step 2, `CHECKS!F`).

The sheet derives a 4-way macro-family (STR/EQU/EQK/SLS) from the combo label text and sets
gammaW = 1.35 (STR), 0.9 (EQU), 1.0 otherwise. `INPUT!I` (the label the sheet parses) reads
"STR EQK" for both `SLV_STR` (STR EQK, 48 rows) and `SLV_EQU` (EQK EQU, 24 rows) — the source
workbook mislabels the second block's own comboType text, so the sheet's own gammaW for `SLV_EQU`
comes out as 1.0 (the "else" branch), same as `SLV_STR`, never the 0.9 an "EQU" label would give;
`famiglia` here is trustworthy (position-based, `docs/architecture-batch2.md §7`) so both modes
agree. This also happens to match NTC2018 §2.5.3 (combinazione sismica, gammaG=gammaQ=1 regardless
of STR/EQU sub-type): no divergence to report for this step."""
from strutture.shared.load_table import Famiglia

GAMMA_STR = 1.35  # NTC2018 Tab. 2.6.I, combinazione fondamentale, A1 - carichi permanenti favorevoli esclusi.
GAMMA_EQU = 0.90  # NTC2018 Tab. 6.2.I, approccio EQU - carichi permanenti stabilizzanti.
GAMMA_SISMICA = 1.0  # NTC2018 §2.5.3 - combinazione sismica, gammaG = gammaQ = 1.


def gamma_permanenti(famiglia: Famiglia, *, legacy_compat: bool) -> float:
    """gammaW for the self-weight of the footing/pedestal/soil, given the combination `famiglia`."""
    if famiglia == "SLU_STR":
        return GAMMA_STR
    if famiglia == "SLU_EQU":
        return GAMMA_EQU
    return GAMMA_SISMICA  # SLV_STR, SLV_EQU, SLE_* (see module docstring: no legacy/fixed divergence)

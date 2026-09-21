import pytest

from strutture.foundations.plinti_isolati.gamma_azioni import GAMMA_EQU, GAMMA_SISMICA, GAMMA_STR, gamma_permanenti


@pytest.mark.golden
def test_gamma_permanenti_str_legacy() -> None:
    assert gamma_permanenti("SLU_STR", legacy_compat=True) == GAMMA_STR


@pytest.mark.unit
@pytest.mark.parametrize(
    ("famiglia", "atteso"),
    [("SLU_STR", GAMMA_STR), ("SLU_EQU", GAMMA_EQU), ("SLV_STR", GAMMA_SISMICA), ("SLV_EQU", GAMMA_SISMICA),
     ("SLE_RARA", GAMMA_SISMICA), ("SLE_FREQ", GAMMA_SISMICA), ("SLE_QP", GAMMA_SISMICA)],
)
def test_gamma_permanenti_stesso_in_entrambe_le_modalita(famiglia: str, atteso: float) -> None:
    """No legacy/fixed divergence in gammaW: see `gamma_azioni.py` module docstring — the source
    workbook mislabels the SLV_EQU block's own text column, so its sheet-computed gammaW already
    equals 1.0 (same as SLV_STR), matching NTC2018 §2.5.3."""
    assert gamma_permanenti(famiglia, legacy_compat=True) == atteso
    assert gamma_permanenti(famiglia, legacy_compat=False) == atteso

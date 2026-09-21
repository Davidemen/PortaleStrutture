import pytest
from pydantic import ValidationError

from strutture.foundations.plinti_isolati.rows import ResistenzaRow, validate_unique_famiglia


@pytest.mark.unit
def test_resistenza_row_valida() -> None:
    row = ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=2.0)
    assert row.famiglia == "SLU_STR"


@pytest.mark.unit
def test_resistenza_row_sigma_non_positiva_rifiutata() -> None:
    with pytest.raises(ValidationError):
        ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=0.0)


@pytest.mark.unit
def test_validate_unique_famiglia_duplicata() -> None:
    rows = (ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=2.0),
            ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=3.0))
    with pytest.raises(ValueError, match="riga 1 e riga 2"):
        validate_unique_famiglia(rows)


@pytest.mark.unit
def test_validate_unique_famiglia_ok() -> None:
    rows = (ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=2.0),
            ResistenzaRow(famiglia="SLU_EQU", sigma_ammissibile=2.0))
    validate_unique_famiglia(rows)  # non deve sollevare

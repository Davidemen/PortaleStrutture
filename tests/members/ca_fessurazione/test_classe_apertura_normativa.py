import pytest

from strutture.members.ca_fessurazione.classe_apertura_normativa import (
    CLASSE_FALLBACK_FRE,
    CLASSE_FALLBACK_QPE,
    classe_normativa_fre,
    classe_normativa_qpe,
)

pytestmark = pytest.mark.unit


def test_default_ordinarie_poco_sensibile_matches_sheet_fallback():
    assert classe_normativa_fre("ordinarie", "poco sensibile") == CLASSE_FALLBACK_FRE == "w3"
    assert classe_normativa_qpe("ordinarie", "poco sensibile") == CLASSE_FALLBACK_QPE == "w2"


def test_molto_aggressive_sensibile_returns_none_for_decompressione():
    assert classe_normativa_fre("molto aggressive", "sensibile") is None
    assert classe_normativa_qpe("molto aggressive", "sensibile") is None

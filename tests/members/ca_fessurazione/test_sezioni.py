import pytest

from strutture.members.ca_fessurazione.sezioni import SEZIONI

pytestmark = pytest.mark.unit


def test_sezioni_has_three_rows():
    assert len(SEZIONI) == 3


def test_sezioni_titoli_e_sottotitoli():
    assert SEZIONI == (
        ("Sezione h = 30 cm", ""),
        ("Sezione h = 30 cm", "Zona centrale"),
        ("Sezione h = 20 cm", ""),
    )


def test_sezioni_blank_subtitles_are_empty_strings_not_zero():
    """Divergence: sheet renders the blank B12/B28 link as literal `0`; we use ""."""
    assert SEZIONI[0][1] == ""
    assert SEZIONI[2][1] == ""

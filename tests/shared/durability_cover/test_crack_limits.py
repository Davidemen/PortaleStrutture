"""Crack-width limit selection tests vs `ca-travi` Tabelle!M56:Q62 (NTC2018 Tab. 4.1.IV)."""
import pytest

from strutture.shared.durability_cover import crack_width_limit

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("condizione", "combinazione", "sensibilita", "expected"),
    [
        ("ordinarie", "frequente", "sensibile", "w2"),
        ("ordinarie", "frequente", "poco sensibile", "w3"),
        ("ordinarie", "quasi permanente", "sensibile", "w1"),
        ("ordinarie", "quasi permanente", "poco sensibile", "w2"),
        ("aggressive", "frequente", "sensibile", "w1"),
        ("aggressive", "frequente", "poco sensibile", "w2"),
        ("aggressive", "quasi permanente", "poco sensibile", "w1"),
        ("molto aggressive", "frequente", "poco sensibile", "w1"),
        ("molto aggressive", "quasi permanente", "poco sensibile", "w1"),
    ],
)
def test_crack_width_limit_matches_sheet(condizione, combinazione, sensibilita, expected):
    assert crack_width_limit(condizione, combinazione, sensibilita) == expected


def test_crack_width_limit_none_when_sheet_cell_blank():
    # "aggressive"/"molto aggressive" + "sensibile" quasi-permanente cells are blank in the
    # sheet: NTC2018 requires a decompression check there, not a crack-width limit.
    assert crack_width_limit("aggressive", "quasi permanente", "sensibile") is None
    assert crack_width_limit("molto aggressive", "frequente", "sensibile") is None
    assert crack_width_limit("molto aggressive", "quasi permanente", "sensibile") is None


def test_crack_width_limit_rejects_unknown_combination():
    with pytest.raises(ValueError):
        crack_width_limit("ordinarie", "rara", "sensibile")  # type: ignore[arg-type]

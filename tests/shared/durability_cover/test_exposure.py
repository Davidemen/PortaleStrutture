"""Exposure-group mapping tests vs Tabelle!M57:N61."""
import pytest

from strutture.shared.durability_cover.exposure import environmental_condition
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("group", "expected"),
    [("a", "ordinarie"), ("b", "aggressive"), ("c", "molto aggressive")],
)
def test_group_maps_to_condition(group, expected):
    assert environmental_condition(group) == expected


def test_unknown_group_raises():
    with pytest.raises(KeyNotFound):
        environmental_condition("d")  # type: ignore[arg-type]

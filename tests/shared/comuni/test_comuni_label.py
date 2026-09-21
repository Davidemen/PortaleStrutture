"""Labels make homonym comuni selectable from one dropdown: 'Castro (Bergamo)' vs 'Castro (Lecce)'."""
import pytest

from strutture.shared.comuni import AmbiguousComuneError, lookup_comune, search_options
from strutture.shared.comuni.label import comune_label, split_label

pytestmark = pytest.mark.unit


def test_split_label_extracts_provincia_only_from_trailing_parentheses() -> None:
    assert split_label("Castro (Bergamo)") == ("Castro", "Bergamo")
    assert split_label("  Reggio nell'Emilia ") == ("Reggio nell'Emilia", None)
    assert split_label("Castro ()") == ("Castro ()", None)


def test_comune_label_adds_provincia_only_for_homonyms() -> None:
    assert comune_label("Castro", "Lecce", is_homonym=True) == "Castro (Lecce)"
    assert comune_label("Bergamo", "Bergamo", is_homonym=False) == "Bergamo"


def test_lookup_accepts_a_label_for_homonyms() -> None:
    with pytest.raises(AmbiguousComuneError):
        lookup_comune("Castro")
    assert lookup_comune("Castro (Lecce)").provincia == "Lecce"
    assert lookup_comune("castro (bergamo)").provincia == "Bergamo"
    assert lookup_comune("Castro (Lecce)", provincia="Bergamo").provincia == "Bergamo"  # explicit provincia wins


def test_search_options_label_round_trips_through_lookup() -> None:
    options = search_options("castro", limit=50)
    labels = [o.label for o in options]
    assert "Castro (Bergamo)" in labels and "Castro (Lecce)" in labels
    assert "Castrovillari" in labels  # unique names stay plain
    for option in options:
        assert lookup_comune(option.label).istat == option.comune.istat

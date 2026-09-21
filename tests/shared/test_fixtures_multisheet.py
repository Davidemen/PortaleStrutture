"""extract.fixtures: overrides and reads may address several sheets ("CHECKS!AA6")."""
import pytest

from extract.fixtures import split_address, split_overrides

pytestmark = pytest.mark.unit


def test_split_address_defaults_to_the_main_sheet() -> None:
    assert split_address("H6", "INPUT") == ("INPUT", "H6")
    assert split_address("CHECKS!AA6", "INPUT") == ("CHECKS", "AA6")
    assert split_address("'LCC Reactions'!B12", "INPUT") == ("LCC Reactions", "B12")


def test_split_overrides_groups_cells_by_sheet() -> None:
    grouped = split_overrides({"H6": 1, "CHECKS!AA6": 2, "'LC Reactions'!C4": 3}, "INPUT")
    assert grouped == {"INPUT": {"H6": 1}, "CHECKS": {"AA6": 2}, "LC Reactions": {"C4": 3}}

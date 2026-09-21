"""Validator unit tests: zone domains, unique istat, no blanks (architecture.md §3, C3)."""
import pytest

from strutture.shared.comuni.validate import validate_rows

pytestmark = pytest.mark.unit

GOOD_ROW = {
    "regione": "Lombardia", "provincia": "Bergamo", "istat": "3016037", "comune": "Brembate",
    "zona_sismica": "4", "zona_vento": "1", "zona_neve": "I (alpina)",
}


def test_valid_rows_have_no_violations():
    assert validate_rows((GOOD_ROW, {**GOOD_ROW, "istat": "3016038", "comune": "Altro"})) == ()


@pytest.mark.parametrize("field", ["regione", "provincia", "istat", "comune", "zona_sismica", "zona_vento", "zona_neve"])
def test_blank_field_is_a_violation(field):
    violations = validate_rows(({**GOOD_ROW, field: ""},))
    assert any(field in v and "blank" in v for v in violations)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [("zona_sismica", "5"), ("zona_sismica", "0"), ("zona_vento", "56"), ("zona_vento", "0"), ("zona_neve", "IV")],
)
def test_out_of_domain_zone_is_a_violation(field, bad_value):
    violations = validate_rows(({**GOOD_ROW, field: bad_value},))
    assert any(field in v for v in violations)


def test_duplicate_istat_is_a_violation():
    rows = (GOOD_ROW, {**GOOD_ROW, "comune": "Duplicato"})
    violations = validate_rows(rows)
    assert any("duplicate istat" in v and "3016037" in v for v in violations)


def test_all_violations_are_reported_not_just_the_first():
    rows = ({**GOOD_ROW, "regione": "", "zona_sismica": "9"},)
    violations = validate_rows(rows)
    assert len(violations) == 2

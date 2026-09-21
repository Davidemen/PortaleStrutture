"""Loader unit/integration tests: CSV parsing, and the public lookup_comune/search_comuni API
against the real built database (src/strutture/data/comuni.csv), covering homonyms and accents.
"""
from pathlib import Path

import pytest
from pydantic import ValidationError

from strutture.shared.comuni import AmbiguousComuneError, Comune, KeyNotFound, lookup_comune, search_comuni
from strutture.shared.comuni.loader import parse_csv

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_parse_csv_builds_frozen_comune_models_with_string_istat():
    comuni = parse_csv(FIXTURES / "comuni_loader_sample.csv")

    assert comuni[0] == Comune(
        regione="Lombardia", provincia="Bergamo", istat="3016037", comune="Brembate",
        zona_sismica=4, zona_vento=1, zona_neve="I (alpina)",
    )
    assert isinstance(comuni[0].istat, str)
    with pytest.raises(ValidationError):
        comuni[0].comune = "changed"  # frozen model


def test_lookup_comune_is_case_and_accent_insensitive():
    canonical = lookup_comune("Milano")
    assert lookup_comune("milano") == canonical
    assert lookup_comune("MILANO") == canonical


def test_lookup_comune_resolves_accented_name():
    result = lookup_comune("Cirò Marina")
    assert result.comune == "Cirò Marina"
    assert lookup_comune("ciro marina") == result


def test_lookup_comune_unknown_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        lookup_comune("Nessundove")


def test_lookup_comune_blank_name_raises_value_error():
    with pytest.raises(ValueError):
        lookup_comune("   ")


def test_lookup_comune_homonym_without_provincia_is_ambiguous():
    with pytest.raises(AmbiguousComuneError):
        lookup_comune("Livo")


def test_lookup_comune_homonym_resolved_by_provincia():
    como = lookup_comune("Livo", provincia="Como")
    trento = lookup_comune("Livo", provincia="Trento")
    assert como.provincia == "Como"
    assert trento.provincia == "Trento"
    assert como.istat != trento.istat


def test_search_comuni_prefix_and_limit():
    results = search_comuni("Berga", limit=5)
    assert 0 < len(results) <= 5
    assert all(r.comune.lower().startswith("berga") for r in results)


def test_search_comuni_invalid_limit_raises():
    with pytest.raises(ValueError):
        search_comuni("Milano", limit=0)

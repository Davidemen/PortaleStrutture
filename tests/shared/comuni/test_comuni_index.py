"""Pure index/resolve/prefix-search unit tests, incl. homonym disambiguation by provincia."""
import pytest

from strutture.shared.comuni.errors import AmbiguousComuneError, KeyNotFound
from strutture.shared.comuni.index import by_normalized_name, filter_prefix, resolve, sorted_by_normalized_name
from strutture.shared.comuni.models import Comune

pytestmark = pytest.mark.unit

LIVO_COMO = Comune(regione="Lombardia", provincia="Como", istat="3013130", comune="Livo",
                    zona_sismica=4, zona_vento=1, zona_neve="I (alpina)")
LIVO_TRENTO = Comune(regione="Trentino-Alto Adige", provincia="Trento", istat="4022106", comune="Livo",
                      zona_sismica=4, zona_vento=1, zona_neve="I (alpina)")
MILANO = Comune(regione="Lombardia", provincia="Milano", istat="3015146", comune="Milano",
                 zona_sismica=4, zona_vento=1, zona_neve="I (mediterranea)")

COMUNI = (LIVO_COMO, LIVO_TRENTO, MILANO)


def test_resolve_unique_name_returns_it_without_provincia():
    matches = by_normalized_name(COMUNI)["milano"]
    assert resolve("Milano", matches, provincia=None) == MILANO


def test_resolve_homonym_without_provincia_is_ambiguous():
    matches = by_normalized_name(COMUNI)["livo"]
    with pytest.raises(AmbiguousComuneError):
        resolve("Livo", matches, provincia=None)


def test_resolve_homonym_with_provincia_disambiguates_case_insensitively():
    matches = by_normalized_name(COMUNI)["livo"]
    assert resolve("Livo", matches, provincia="trento") == LIVO_TRENTO
    assert resolve("Livo", matches, provincia="COMO") == LIVO_COMO


def test_resolve_no_match_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        resolve("Nowhere", (), provincia=None)


def test_resolve_wrong_provincia_raises_key_not_found():
    matches = by_normalized_name(COMUNI)["livo"]
    with pytest.raises(KeyNotFound):
        resolve("Livo", matches, provincia="Bergamo")


def test_filter_prefix_matches_case_and_accent_insensitively():
    pairs = sorted_by_normalized_name(COMUNI)
    assert filter_prefix(pairs, "MIL", limit=10) == (MILANO,)


def test_filter_prefix_respects_limit_and_sort_order():
    pairs = sorted_by_normalized_name(COMUNI)
    result = filter_prefix(pairs, "li", limit=1)
    assert result == (LIVO_COMO,)  # "livo" (como) sorts before "livo" (trento) only by stable tuple order

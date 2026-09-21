import pytest

from strutture.loads.sisma.comune_info import risolvi_comune
from strutture.shared.comuni import AmbiguousComuneError, KeyNotFound


@pytest.mark.unit
def test_resolves_known_comune():
    match = risolvi_comune("Brembate")
    assert match.provincia == "Bergamo"
    assert match.regione == "Lombardia"
    assert match.zona_sismica == 4


@pytest.mark.unit
def test_disambiguates_via_provincia():
    match = risolvi_comune("Roma", "Roma")
    assert match.regione == "Lazio"


@pytest.mark.unit
def test_unknown_comune_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        risolvi_comune("NonEsisteSicuramente9999")


@pytest.mark.unit
def test_case_insensitive_and_accent_insensitive():
    match = risolvi_comune("BREMBATE")
    assert match.provincia == "Bergamo"


@pytest.mark.unit
def test_homonym_across_province_raises_ambiguous_without_disambiguation():
    with pytest.raises(AmbiguousComuneError):
        risolvi_comune("Brione")

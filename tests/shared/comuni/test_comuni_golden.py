"""Golden cases: the comuni used by the sisma/neve/vento spec §Golden test case sections, so the
comuni module stays consistent with what the downstream tool specs assume.
"""
import pytest

from strutture.shared.comuni import lookup_comune

pytestmark = pytest.mark.golden


def test_brembate_golden_case_from_sisma_spec():
    # sisma.md §Golden test case: comune=Brembate -> provincia=Bergamo, regione=Lombardia
    comune = lookup_comune("Brembate")
    assert comune.provincia == "Bergamo"
    assert comune.regione == "Lombardia"


def test_mapello_golden_case_from_neve_spec():
    # neve.md §Golden test case (Tool 1): comune=Mapello -> provincia=Bergamo, regione=Lombardia,
    # zona="I (alpina)"
    comune = lookup_comune("Mapello")
    assert comune.provincia == "Bergamo"
    assert comune.regione == "Lombardia"
    assert comune.zona_neve == "I (alpina)"


def test_bergamo_golden_case_from_neve_spec():
    # neve.md §Golden test case (Tool 2): comune=Bergamo -> zona="I (alpina)"
    comune = lookup_comune("Bergamo")
    assert comune.provincia == "Bergamo"
    assert comune.regione == "Lombardia"
    assert comune.zona_neve == "I (alpina)"


def test_milano_golden_case_from_vento_spec():
    # vento.md §8 Golden test case: H4="Milano" -> H5(provincia)="Milano", H6(regione)="Lombardia",
    # H7(zona)=1
    comune = lookup_comune("Milano")
    assert comune.provincia == "Milano"
    assert comune.regione == "Lombardia"
    assert comune.zona_vento == 1

import pytest

from strutture.foundations.plinti_isolati.legacy_units import kpa_to_kgcm2
from strutture.foundations.plinti_isolati.pressione_contatto import pressione_contatto


@pytest.mark.golden
def test_pressione_contatto_golden_sovrapposizione() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: sigma_t,total = 1.66283 kg/cm2."""
    pressione = pressione_contatto(2596.93, 40.9685, 1.42918, 4.0, 4.0,
                                    metodo_pressioni="sovrapposizione", legacy_compat=True)
    assert kpa_to_kgcm2(pressione.sigma_max_kpa, legacy_compat=True) == pytest.approx(1.66283, rel=1e-4)
    assert pressione.compressed_ratio == pytest.approx(1.0)


@pytest.mark.unit
def test_pressione_contatto_legacy_forza_sovrapposizione() -> None:
    """legacy_compat=True forces the sheet's method regardless of `metodo_pressioni` (§9-D2)."""
    esatta = pressione_contatto(2596.93, 40.9685, 1.42918, 4.0, 4.0,
                                 metodo_pressioni="esatto", legacy_compat=True)
    legacy = pressione_contatto(2596.93, 40.9685, 1.42918, 4.0, 4.0,
                                 metodo_pressioni="sovrapposizione", legacy_compat=True)
    assert esatta.metodo == "sovrapposizione"
    assert esatta.sigma_max_kpa == pytest.approx(legacy.sigma_max_kpa)


@pytest.mark.unit
def test_pressione_contatto_metodo_esatto_non_forzato() -> None:
    pressione = pressione_contatto(2596.93, 40.9685, 1.42918, 4.0, 4.0,
                                    metodo_pressioni="esatto", legacy_compat=False)
    assert pressione.metodo == "esatto"

import pytest

from strutture.foundations.plinti_isolati.legacy_units import kgcm2_to_kpa, kpa_to_kgcm2, sigma_ammissibile_kpa


@pytest.mark.unit
def test_kpa_to_kgcm2_legacy_factor_10() -> None:
    """docs/architecture-batch2.md note: the sheet approximates 1 MPa = 10 kg/cm2 (exact: 10.1972)."""
    assert kpa_to_kgcm2(1000.0, legacy_compat=True) == pytest.approx(10.0)


@pytest.mark.unit
def test_kpa_to_kgcm2_esatto() -> None:
    assert kpa_to_kgcm2(1000.0, legacy_compat=False) == pytest.approx(10.1972, rel=1e-4)


@pytest.mark.unit
def test_kgcm2_to_kpa_round_trip() -> None:
    for legacy in (True, False):
        valore = kgcm2_to_kpa(2.0, legacy_compat=legacy)
        assert kpa_to_kgcm2(valore, legacy_compat=legacy) == pytest.approx(2.0)


@pytest.mark.unit
def test_sigma_ammissibile_kpa_si_non_legacy_passa_diretto() -> None:
    assert sigma_ammissibile_kpa(200.0, sistema_unita="SI", legacy_compat=False) == 200.0


@pytest.mark.unit
def test_sigma_ammissibile_kpa_tecnico_converte() -> None:
    assert sigma_ammissibile_kpa(2.0, sistema_unita="tecnico", legacy_compat=False) == pytest.approx(196.133, rel=1e-4)


@pytest.mark.unit
def test_sigma_ammissibile_kpa_legacy_forza_tecnico() -> None:
    """legacy_compat=True treats the value as kg/cm2 (sheet convention) even if sistema_unita='SI'."""
    assert sigma_ammissibile_kpa(2.0, sistema_unita="SI", legacy_compat=True) == pytest.approx(200.0)

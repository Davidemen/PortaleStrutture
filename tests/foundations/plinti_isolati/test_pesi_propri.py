import pytest

from strutture.foundations.plinti_isolati.pesi_propri import pesi_propri


@pytest.mark.golden
def test_pesi_propri_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: Wplinth=320, Wped=0, Wearth=1440 kN."""
    pesi = pesi_propri(4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 20.0)
    assert pesi.w_plinto_kN == pytest.approx(320.0, rel=1e-6)
    assert pesi.w_pedestal_kN == pytest.approx(0.0, abs=1e-9)
    assert pesi.w_terreno_kN == pytest.approx(1440.0, rel=1e-6)


@pytest.mark.unit
def test_pesi_propri_con_bicchiere() -> None:
    """A pedestal contributes its own weight and is excluded from the soil-cover area."""
    pesi = pesi_propri(4.0, 4.0, 0.8, 4.5, 1.0, 1.0, 0.5, 0.5, 20.0)
    assert pesi.w_pedestal_kN == pytest.approx(1.0 * 1.0 * 1.0 * 25.0)
    assert pesi.w_terreno_kN == pytest.approx((16.0 - 1.0) * 4.5 * 20.0)


@pytest.mark.unit
def test_pesi_propri_dimensioni_non_positive() -> None:
    with pytest.raises(ValueError):
        pesi_propri(0.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 20.0)

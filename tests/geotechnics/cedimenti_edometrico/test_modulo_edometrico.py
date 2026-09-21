"""Unit tests for `eed_kpa` — never a silent 0 (docs/architecture-batch2.md §7 "edometrico J")."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.modulo_edometrico import eed_kpa
from strutture.shared.soil_layers import SoilLayer
from strutture.shared.tables import KeyNotFound
from strutture.shared.units import mpa_to_kpa

_LAYERS = (
    SoilLayer(z_top_m=0.0, z_bot_m=3.7, modulo_MPa=5.5),
    SoilLayer(z_top_m=3.7, z_bot_m=4.7, modulo_MPa=7.0),
)


@pytest.mark.unit
def test_returns_converted_modulus_when_covered() -> None:
    assert eed_kpa(_LAYERS, 2.0, legacy=False) == pytest.approx(mpa_to_kpa(5.5))


@pytest.mark.unit
def test_raises_key_not_found_past_coverage_when_not_legacy() -> None:
    with pytest.raises(KeyNotFound):
        eed_kpa(_LAYERS, 10.0, legacy=False)


@pytest.mark.unit
def test_returns_none_past_coverage_in_legacy_mode() -> None:
    assert eed_kpa(_LAYERS, 10.0, legacy=True) is None

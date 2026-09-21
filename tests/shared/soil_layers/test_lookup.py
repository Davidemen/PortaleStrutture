"""`layer_at`: coverage lookup that never returns 0 silently (docs/architecture-batch2.md §7)."""
import pytest

from strutture.shared.soil_layers import SoilLayer, layer_at
from strutture.shared.tables import KeyNotFound

LAYERS = (
    SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),
    SoilLayer(z_top_m=1.0, z_bot_m=2.5, modulo_MPa=12.0),
    SoilLayer(z_top_m=2.5, z_bot_m=5.0, modulo_MPa=15.0),
)


@pytest.mark.unit
def test_finds_layer_by_depth() -> None:
    assert layer_at(LAYERS, 0.5) is LAYERS[0]
    assert layer_at(LAYERS, 2.0) is LAYERS[1]
    assert layer_at(LAYERS, 4.9) is LAYERS[2]


@pytest.mark.unit
def test_first_layer_is_inclusive_at_z_zero() -> None:
    """Row-0 boundary special case (spec §"Row-0 boundary special case"): z=0 belongs to layer 1,
    which uses `[z_top, z_bot]` (closed at both ends) unlike every other layer's `(z_top, z_bot]`."""
    assert layer_at(LAYERS, 0.0) is LAYERS[0]


@pytest.mark.unit
def test_layer_boundary_belongs_to_the_upper_layer() -> None:
    assert layer_at(LAYERS, 1.0) is LAYERS[0]
    assert layer_at(LAYERS, 2.5) is LAYERS[1]


@pytest.mark.unit
def test_raises_key_not_found_past_coverage() -> None:
    with pytest.raises(KeyNotFound, match="non copre"):
        layer_at(LAYERS, 5.1)


@pytest.mark.unit
def test_legacy_mode_returns_none_instead_of_raising() -> None:
    assert layer_at(LAYERS, 5.1, legacy=True) is None


@pytest.mark.unit
def test_raises_key_not_found_in_a_gap() -> None:
    gapped = (
        SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),
        SoilLayer(z_top_m=1.5, z_bot_m=3.0, modulo_MPa=12.0),
    )
    with pytest.raises(KeyNotFound):
        layer_at(gapped, 1.2)

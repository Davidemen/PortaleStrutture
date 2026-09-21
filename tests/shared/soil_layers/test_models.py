"""`SoilLayer` field/row validation."""
import pytest
from pydantic import ValidationError

from strutture.shared.soil_layers import SoilLayer


@pytest.mark.unit
def test_valid_layer() -> None:
    layer = SoilLayer(z_top_m=0.0, z_bot_m=1.5, modulo_MPa=10.0)
    assert layer.z_top_m == 0.0
    assert layer.z_bot_m == 1.5
    assert layer.modulo_MPa == 10.0


@pytest.mark.unit
def test_is_frozen() -> None:
    layer = SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=5.0)
    with pytest.raises(ValidationError):
        layer.z_top_m = 1.0  # type: ignore[misc]


@pytest.mark.unit
def test_rejects_negative_top() -> None:
    with pytest.raises(ValidationError):
        SoilLayer(z_top_m=-0.1, z_bot_m=1.0, modulo_MPa=5.0)


@pytest.mark.unit
def test_rejects_non_positive_modulus() -> None:
    with pytest.raises(ValidationError):
        SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=0.0)


@pytest.mark.unit
def test_rejects_bottom_not_below_top() -> None:
    with pytest.raises(ValidationError, match="strato"):
        SoilLayer(z_top_m=1.0, z_bot_m=1.0, modulo_MPa=5.0)

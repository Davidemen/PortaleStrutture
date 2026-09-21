import pytest
from pydantic import ValidationError

from strutture.loads.vento_cpe.models import VentoCpeInput


@pytest.mark.unit
def test_input_rejects_non_positive_b():
    with pytest.raises(ValidationError):
        VentoCpeInput(b=0, d=12, h=9)


@pytest.mark.unit
def test_input_rejects_non_positive_d():
    with pytest.raises(ValidationError):
        VentoCpeInput(b=15, d=-1, h=9)


@pytest.mark.unit
def test_input_rejects_non_positive_h():
    with pytest.raises(ValidationError):
        VentoCpeInput(b=15, d=12, h=0)


@pytest.mark.unit
def test_input_is_frozen():
    inputs = VentoCpeInput(b=15, d=12, h=9)
    with pytest.raises(ValidationError):
        inputs.b = 20

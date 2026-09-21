"""biaxial(): the esatto dispatcher (kern check -> Navier or no-tension solver)."""
import pytest

from strutture.shared.footing_pressure.biaxial import biaxial
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit


def test_in_kern_dispatches_to_navier():
    result = biaxial(n_kn=1000.0, mx_knm=100.0, my_knm=100.0, bx_m=4.0, by_m=4.0)
    assert result.in_kern is True
    assert result.neutral_axis is None


def test_outside_kern_dispatches_to_no_tension_solver():
    result = biaxial(n_kn=1000.0, mx_knm=1000.0, my_knm=1000.0, bx_m=4.0, by_m=4.0)
    assert result.in_kern is False
    assert result.neutral_axis is not None
    assert result.sigma_min_kpa == 0.0


def test_resultant_outside_footing_raises_calc_error():
    with pytest.raises(CalcError):
        biaxial(n_kn=1000.0, mx_knm=0.0, my_knm=1000.0 * 2.5, bx_m=4.0, by_m=6.0)  # ex=2.5 >= bx/2=2.0


@pytest.mark.parametrize(("bx_m", "by_m"), [(0.0, 4.0), (-1.0, 4.0), (4.0, 0.0), (4.0, -1.0)])
def test_rejects_invalid_geometry(bx_m, by_m):
    with pytest.raises(ValueError):
        biaxial(n_kn=1000.0, mx_knm=0.0, my_knm=0.0, bx_m=bx_m, by_m=by_m)

import pytest

from strutture.loads.sisma.campionamento import campiona_periodi


@pytest.mark.unit
def test_default_grid_is_81_points_0_to_4_step_0_05():
    points = campiona_periodi(0.0, 4.0, 0.05)
    assert len(points) == 81
    assert points[0] == pytest.approx(0.0)
    assert points[-1] == pytest.approx(4.0)
    assert points[1] == pytest.approx(0.05)


@pytest.mark.unit
def test_grid_is_immutable_tuple():
    points = campiona_periodi(0.0, 1.0, 0.5)
    assert isinstance(points, tuple)
    assert points == (0.0, 0.5, 1.0)

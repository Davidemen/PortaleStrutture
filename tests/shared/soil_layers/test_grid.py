"""`depth_grid`: replaces the sheets' hardcoded fill-down (10 cm step, fixed row count)."""
import pytest

from strutture.shared.soil_layers import depth_grid


@pytest.mark.unit
def test_exact_multiple() -> None:
    assert depth_grid(1.0, 0.25) == (0.0, 0.25, 0.5, 0.75, 1.0)


@pytest.mark.unit
def test_matches_elastico_centro_grid_size() -> None:
    """`Elastico_centrale_Newmark`: z=10..910 cm step 10 cm -> 91 stress-integration rows (§ input
    table), i.e. `depth_grid(9.1, 0.1)[1:]` has 91 points."""
    grid = depth_grid(9.1, 0.1)
    assert len(grid) == 92  # including the z=0 surface point
    assert len(grid[1:]) == 91
    assert grid[-1] == pytest.approx(9.1)


@pytest.mark.unit
def test_non_exact_multiple_appends_remainder() -> None:
    grid = depth_grid(1.0, 0.3)
    assert grid[:-1] == pytest.approx((0.0, 0.3, 0.6, 0.9))
    assert grid[-1] == pytest.approx(1.0)


@pytest.mark.unit
@pytest.mark.parametrize("z_max_m,dz_m", [(0.0, 0.1), (-1.0, 0.1), (1.0, 0.0), (1.0, -0.1)])
def test_rejects_non_positive_inputs(z_max_m: float, dz_m: float) -> None:
    with pytest.raises(ValueError):
        depth_grid(z_max_m, dz_m)

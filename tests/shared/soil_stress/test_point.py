"""`under_point`: signed 4-sub-rectangle Fadum superposition.

The sheet `500`'s own golden case is symmetric (F7=F8=F9=F10, docs/specs/geo-cedimenti-elastico.md
"PUNTO axis pairing unverified for off-center points") so a same-side vs. cross-side pairing bug is
numerically invisible there. These hand-computed asymmetric cases (interior and exterior point)
are cross-checked against a direct numerical double integral of the Boussinesq point-load kernel
over the loaded rectangle, independent of `newmark_corner`'s own closed form — see
`docs/divergences/soil-stress-fadum-superposition.md`."""
import pytest
from pydantic import ValidationError

from strutture.shared.soil_stress import PointStress, under_point
from strutture.shared.soil_stress.newmark import newmark_corner


@pytest.mark.unit
def test_asymmetric_interior_point_matches_brute_force_integral() -> None:
    # B=6m, L=4m, q=100kPa, point at (1, 1) from the (0,0) corner, z=2m.
    # Brute-force double integral of 3*q*z^3 / (2*pi*((x-x0)^2+(y-y0)^2+z^2)^2.5) over [0,6]x[0,4]:
    # 57.84643 kPa (1200x1200 midpoint rule); Fadum superposition below reproduces it to 1e-4.
    result = under_point(100.0, 6.0, 4.0, 1.0, 1.0, 2.0)
    assert result.total == pytest.approx(57.8464, rel=2e-4)
    assert sum(result.parts) == pytest.approx(result.total, rel=1e-12)


@pytest.mark.unit
def test_asymmetric_exterior_point_matches_brute_force_integral() -> None:
    # Same rectangle, point at x=-1 (1m beyond the B=0 edge), y=1 (inside), z=2m: brute-force
    # integral = 15.0638 kPa; the signed superposition below (some parts negative) must match.
    result = under_point(100.0, 6.0, 4.0, -1.0, 1.0, 2.0)
    assert result.total == pytest.approx(15.0638, rel=2e-4)
    assert any(part < 0 for part in result.parts)


@pytest.mark.unit
def test_interior_point_decomposes_into_four_positive_parts() -> None:
    result = under_point(80.0, 10.0, 8.0, 3.0, 5.0, 1.5)
    assert all(part > 0 for part in result.parts)
    assert result.total == pytest.approx(sum(result.parts))


@pytest.mark.unit
def test_pairs_one_segment_from_each_side_not_same_side() -> None:
    """The fixed pairing (each part crosses the x-split with the y-split) never reduces to the
    sheet's buggy same-side pairing, which would combine the two x-splits (or the two y-splits)
    into one rectangle — an operation `under_point` never performs."""
    q, b, l, x, y, z = 100.0, 8.0, 6.0, 3.0, 2.0, 1.0
    result = under_point(q, b, l, x, y, z)
    same_side_x = newmark_corner(q, x, b - x, z)  # the sheet's "Ofga"-style same-side rectangle
    same_side_y = newmark_corner(q, y, l - y, z)  # the sheet's "Ocde"-style same-side rectangle
    assert result.total != pytest.approx(same_side_x + same_side_y)


@pytest.mark.unit
def test_center_point_equals_under_center_via_four_equal_parts() -> None:
    from strutture.shared.soil_stress import under_center

    b, l, z, q = 3.5, 5.0, 1.2, 90.0
    result = under_point(q, b, l, b / 2, l / 2, z)
    assert result.total == pytest.approx(under_center(q, b, l, z), rel=1e-9)
    assert len({round(part, 9) for part in result.parts}) == 1


@pytest.mark.unit
def test_point_exactly_on_the_rectangle_edge_zeroes_that_split() -> None:
    """x=0 (on the B=0 edge): the a1 split has zero width, so both parts pairing with it vanish
    and the total collapses to the two parts using the full-width a2 split."""
    result = under_point(100.0, 8.0, 6.0, 0.0, 2.0, 1.0)
    assert result.parts[0] == 0.0
    assert result.parts[2] == 0.0
    assert result.total == pytest.approx(result.parts[1] + result.parts[3])


@pytest.mark.unit
def test_output_is_frozen_point_stress_model() -> None:
    result = under_point(50.0, 4.0, 4.0, 2.0, 2.0, 1.0)
    assert isinstance(result, PointStress)
    with pytest.raises(ValidationError):
        result.total = 0.0  # type: ignore[misc]

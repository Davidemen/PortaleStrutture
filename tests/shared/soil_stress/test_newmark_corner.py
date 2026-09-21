"""`newmark_corner` against the sheet's own computed values (`build/data/geo-cedimenti/500.csv`,
sub-rectangle "Ofga") and a textbook reference point."""
import csv
import math
from pathlib import Path

import pytest

from strutture.shared.soil_stress import newmark_corner
from strutture.shared.soil_stress.newmark import _arctan_branch
from strutture.shared.units import cm_to_m, kgcm2_to_kpa

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "soil_stress_newmark_corner_500.csv"


def _rows() -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.golden
@pytest.mark.parametrize("row", _rows(), ids=lambda row: f"z={row['z_cm']}cm")
def test_matches_sheet_500_ofga_column(row: dict[str, str]) -> None:
    q_kpa = kgcm2_to_kpa(float(row["q_kgcm2"]))
    a_m, b_m, z_m = cm_to_m(float(row["a_cm"])), cm_to_m(float(row["b_cm"])), cm_to_m(float(row["z_cm"]))
    expected = kgcm2_to_kpa(float(row["iz_times_q_kgcm2"]))
    assert newmark_corner(q_kpa, a_m, b_m, z_m) == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
def test_textbook_square_corner_factor() -> None:
    """Iz(m=1, n=1) = 0.175 is the standard tabulated corner-influence-factor reference value."""
    iz = newmark_corner(1.0, 1.0, 1.0, 1.0)
    assert iz == pytest.approx(0.1752, abs=1e-4)


@pytest.mark.unit
def test_zero_width_rectangle_has_no_stress() -> None:
    assert newmark_corner(100.0, 0.0, 5.0, 2.0) == 0.0


@pytest.mark.unit
def test_scales_linearly_with_q() -> None:
    base = newmark_corner(1.0, 3.0, 4.0, 2.0)
    assert newmark_corner(250.0, 3.0, 4.0, 2.0) == pytest.approx(250.0 * base, rel=1e-9)


@pytest.mark.unit
def test_den_equals_num_branch_does_not_raise() -> None:
    """Construct a, b, z with den == num exactly (m=n, den=1+2m², num=m^4; equal when m^4-2m²-1=0,
    m² = 1+√2) to exercise the singular arctan branch without a ZeroDivisionError."""
    m_squared = 1 + math.sqrt(2)
    m = math.sqrt(m_squared)
    z = 1.0
    value = newmark_corner(1.0, m * z, m * z, z)
    assert math.isfinite(value)
    assert 0 < value < 1.0


@pytest.mark.unit
def test_arctan_branch_at_exact_singularity() -> None:
    """`den == num` exactly (a case float rounding through sqrt/division rarely hits): the atan
    term is the pi/2 continuity limit, not a division by zero."""
    assert _arctan_branch(1.0, 2.0, den=5.0, num=5.0, sqrt_den=math.sqrt(5.0)) == pytest.approx(math.pi / 2)


@pytest.mark.unit
def test_rejects_negative_side_lengths() -> None:
    with pytest.raises(ValueError, match="a_m, b_m"):
        newmark_corner(100.0, -1.0, 1.0, 1.0)


@pytest.mark.unit
@pytest.mark.parametrize("z_m", [0.0, -1.0])
def test_rejects_non_positive_depth(z_m: float) -> None:
    with pytest.raises(ValueError, match="z_m"):
        newmark_corner(100.0, 1.0, 1.0, z_m)

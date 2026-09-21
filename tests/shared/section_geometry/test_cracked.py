"""Cracked-section tests: golden case from docs/specs/ca-travi.md Tool 4 (§8), plus a
hand-computed doubly-reinforced case and invalid-input checks.
"""
import math

import pytest

from strutture.shared.section_geometry import cracked_neutral_axis

pytestmark = pytest.mark.unit


def test_singly_reinforced_matches_ca_travi_spec_golden_case():
    # docs/specs/ca-travi.md Tool 4: B[H6]=600, d[Z31]=330, As,o[AM32]=5*Ø20 -> y[Z38]=126.44mm.
    b_mm, d_mm = 600.0, 330.0
    as_mm2 = 5 * math.pi / 4 * 20.0**2
    result = cracked_neutral_axis(b_mm, d_mm, 0.0, as_mm2, 0.0, n=15.0)
    assert result.x_mm == pytest.approx(126.44, rel=1e-4)


def test_singly_reinforced_satisfies_first_moment_equilibrium():
    # 0.5*b*x^2 = n*As*(d-x) must hold at the root (independent hand-check of the formula).
    b_mm, d_mm, as_mm2, n = 300.0, 450.0, 1200.0, 15.0
    result = cracked_neutral_axis(b_mm, d_mm, 0.0, as_mm2, 0.0, n=n)
    lhs = 0.5 * b_mm * result.x_mm**2
    rhs = n * as_mm2 * (d_mm - result.x_mm)
    assert lhs == pytest.approx(rhs, rel=1e-9)
    expected_inertia = b_mm * result.x_mm**3 / 3.0 + n * as_mm2 * (d_mm - result.x_mm) ** 2
    assert result.inertia_cracked_mm4 == pytest.approx(expected_inertia, rel=1e-9)


def test_doubly_reinforced_satisfies_first_moment_equilibrium():
    b_mm, d_mm, d2_mm, as_mm2, as2_mm2, n = 300.0, 450.0, 40.0, 1200.0, 400.0, 15.0
    result = cracked_neutral_axis(b_mm, d_mm, d2_mm, as_mm2, as2_mm2, n=n)
    lhs = 0.5 * b_mm * result.x_mm**2 + (n - 1) * as2_mm2 * (result.x_mm - d2_mm)
    rhs = n * as_mm2 * (d_mm - result.x_mm)
    assert lhs == pytest.approx(rhs, rel=1e-9)


@pytest.mark.parametrize(
    ("b", "d", "d2", "as_", "as2"),
    [
        (0.0, 330.0, 0.0, 1000.0, 0.0),
        (600.0, 0.0, 0.0, 1000.0, 0.0),
        (600.0, 330.0, 330.0, 1000.0, 100.0),  # d2 >= d
        (600.0, 330.0, 0.0, -1.0, 0.0),
        (600.0, 330.0, 0.0, 0.0, 0.0),  # no steel at all
    ],
)
def test_rejects_invalid_inputs(b, d, d2, as_, as2):
    with pytest.raises(ValueError):
        cracked_neutral_axis(b, d, d2, as_, as2)


def test_rejects_non_positive_n():
    with pytest.raises(ValueError):
        cracked_neutral_axis(600.0, 330.0, 0.0, 1000.0, 0.0, n=0.0)

import pytest

from strutture.geotechnics.cedimenti_elastico.steinbrenner_factors import (
    aspect_ratio,
    depth_ratio_bordo,
    depth_ratio_centro,
    influence_factors,
)


@pytest.mark.golden
def test_legacy_matches_the_timoshenko_goodier_3_golden_case():
    a = aspect_ratio(1.0, 1.0)
    b_centro, b_bordo = depth_ratio_centro(5.0, 1.0), depth_ratio_bordo(5.0, 1.0)
    assert a == 1.0
    assert b_centro == 10.0
    assert b_bordo == 5.0
    is_centro, is_bordo = influence_factors(a, b_centro, b_bordo, 0.35, legacy_compat=True)
    assert is_centro == pytest.approx(0.505131, rel=1e-6)
    assert is_bordo == pytest.approx(0.451165, rel=1e-6)


@pytest.mark.unit
def test_code_standard_bordo_uses_edge_midpoint_superposition_not_the_corner_factor():
    # Square footing, H=5B, mu=0.35: legacy reuses the corner factor of the whole B x L rectangle
    # (0.451165), the true edge-midpoint factor from 2 B x (L/2) sub-rectangles is ~31% higher.
    a = aspect_ratio(1.0, 1.0)
    b_bordo = depth_ratio_bordo(5.0, 1.0)
    _, legacy_is_bordo = influence_factors(a, 10.0, b_bordo, 0.35, legacy_compat=True)
    _, fixed_is_bordo = influence_factors(a, 10.0, b_bordo, 0.35, legacy_compat=False)
    assert legacy_is_bordo == pytest.approx(0.451165, rel=1e-6)
    assert fixed_is_bordo == pytest.approx(0.654946, rel=1e-6)
    assert fixed_is_bordo > legacy_is_bordo


@pytest.mark.unit
def test_is_centro_is_unaffected_by_legacy_compat():
    a = aspect_ratio(1.0, 1.0)
    b_centro, b_bordo = depth_ratio_centro(5.0, 1.0), depth_ratio_bordo(5.0, 1.0)
    legacy_is_centro, _ = influence_factors(a, b_centro, b_bordo, 0.35, legacy_compat=True)
    fixed_is_centro, _ = influence_factors(a, b_centro, b_bordo, 0.35, legacy_compat=False)
    assert legacy_is_centro == fixed_is_centro == pytest.approx(0.505131, rel=1e-6)

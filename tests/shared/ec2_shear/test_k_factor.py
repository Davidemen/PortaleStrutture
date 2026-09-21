"""§6.2.2(1) size-effect factor k = min(1 + sqrt(200/d), 2.0)."""
import pytest

from strutture.shared.ec2_shear import k_size


def test_k_matches_shotblast_golden_case():
    """docs/specs/ca-punzonamento.md golden case: d=430 mm -> k used inside uRd,i (AR99-style clause)."""
    assert k_size(430.0) == pytest.approx(1.0 + (200.0 / 430.0) ** 0.5, rel=1e-9)


def test_k_is_capped_at_two():
    assert k_size(50.0) == pytest.approx(2.0)


def test_k_below_cap():
    assert k_size(1000.0) == pytest.approx(1.0 + (0.2**0.5))


@pytest.mark.parametrize("d_mm", [0.0, -10.0])
def test_k_rejects_non_positive_depth(d_mm):
    with pytest.raises(ValueError, match="positive"):
        k_size(d_mm)

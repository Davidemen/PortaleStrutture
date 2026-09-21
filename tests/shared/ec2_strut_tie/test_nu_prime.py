"""§6.5.2(1) nu' = 1 - fck/250."""
import pytest

from strutture.shared.ec2_strut_tie import nu_prime


def test_nu_prime_matches_hand_computation():
    assert nu_prime(35.0) == pytest.approx(1.0 - 35.0 / 250.0)


def test_nu_prime_rejects_non_positive_fck():
    with pytest.raises(ValueError):
        nu_prime(0.0)

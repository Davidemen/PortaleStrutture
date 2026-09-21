"""Unit tests for `coefficienti_sismici`/`kae_mononobe_okabe` (NTC2018 §7.11.6.2.1, rows 80-81/87-88)."""
import math

import pytest

from strutture.members.muro.mononobe_okabe import coefficienti_sismici, kae_mononobe_okabe

pytestmark = pytest.mark.unit


def test_coefficienti_sismici_sisma_1_tratto_a():
    result = coefficienti_sismici(s=1.5, ag_g=0.136, beta_m=0.24, segno_kv=1.0)
    assert result.kh == pytest.approx(0.04896, rel=1e-5)
    assert result.kv == pytest.approx(0.02448, rel=1e-5)
    assert result.theta_rad == pytest.approx(0.0477538, rel=1e-5)


def test_coefficienti_sismici_sisma_2_has_negative_kv():
    result = coefficienti_sismici(s=1.5, ag_g=0.136, beta_m=0.24, segno_kv=-1.0)
    assert result.kv == pytest.approx(-0.02448, rel=1e-5)
    assert result.theta_rad == pytest.approx(0.0501465, rel=1e-5)


def test_kae_mononobe_okabe_tratto_a_sisma_1():
    phi_d = math.radians(30.69) / 1.25
    delta_d = 0.0
    ka = kae_mononobe_okabe(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=0.0, psi_rad=math.radians(90), theta_rad=0.0477538)
    assert ka == pytest.approx(0.445069, rel=1e-5)


def test_kae_reduces_to_ka_coulomb_when_theta_is_zero():
    """θ=0 (no seismic acceleration) -> Mononobe-Okabe collapses to the static Coulomb formula."""
    from strutture.members.muro.coulomb import ka_coulomb

    phi_d, delta_d, beta, psi = math.radians(28), math.radians(5), math.radians(3), math.radians(85)
    assert kae_mononobe_okabe(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta, psi_rad=psi, theta_rad=0.0) == pytest.approx(
        ka_coulomb(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta, psi_rad=psi)
    )

import pytest

from strutture.members.ca_fessurazione.deformazione_media import deformazione_media_armatura

pytestmark = pytest.mark.unit


def test_deformazione_media_tension_stiffening_branch():
    result = deformazione_media_armatura(
        sigma_s_MPa=286, kt=0.4, fctm_MPa=2.834993141272844, rho_eff=0.0270578145405644, alpha_e=6.444068528566923, es_MPa=210000
    )
    assert result == pytest.approx(0.00112753, rel=1e-5)


def test_deformazione_media_minimum_branch_dominates():
    """With a large tension-stiffening term the 0.6*sigma_s/Es floor wins."""
    result = deformazione_media_armatura(sigma_s_MPa=100, kt=1.0, fctm_MPa=10.0, rho_eff=0.001, alpha_e=6.0, es_MPa=210000)
    assert result == pytest.approx(0.6 * 100 / 210000, rel=1e-9)


def test_deformazione_media_rejects_non_positive_rho():
    with pytest.raises(ValueError, match="rho_eff"):
        deformazione_media_armatura(sigma_s_MPa=286, kt=0.4, fctm_MPa=2.8, rho_eff=0, alpha_e=6.4, es_MPa=210000)


def test_deformazione_media_rejects_non_positive_es():
    with pytest.raises(ValueError, match="es_MPa"):
        deformazione_media_armatura(sigma_s_MPa=286, kt=0.4, fctm_MPa=2.8, rho_eff=0.02, alpha_e=6.4, es_MPa=0)

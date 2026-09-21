import pytest

from strutture.geotechnics.cedimenti_elastico.weighted_es import es_weighted_modulus, legacy_weighted_modulus
from strutture.shared.soil_layers import SoilLayer
from strutture.shared.tables import KeyNotFound


@pytest.mark.golden
def test_legacy_matches_the_timoshenko_goodier_3_golden_h11():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=1.60, modulo_MPa=180 * 0.0980665), SoilLayer(z_top_m=1.60, z_bot_m=4.50, modulo_MPa=140 * 0.0980665))
    assert legacy_weighted_modulus(layers, h_m=5.0) == pytest.approx(138.8 * 0.0980665, rel=1e-6)


@pytest.mark.unit
def test_legacy_ignores_layers_beyond_the_first_four_even_if_they_reach_h():
    layers = tuple(SoilLayer(z_top_m=float(i), z_bot_m=float(i + 1), modulo_MPa=10.0 + i) for i in range(6))
    legacy = legacy_weighted_modulus(layers, h_m=6.0)
    fixed = es_weighted_modulus(layers, h_m=6.0, legacy_compat=False)
    assert legacy == pytest.approx((10 + 11 + 12 + 13) / 6, rel=1e-9)
    assert fixed == pytest.approx((10 + 11 + 12 + 13 + 14 + 15) / 6, rel=1e-9)
    assert legacy < fixed


@pytest.mark.unit
def test_code_standard_raises_when_stratigraphy_does_not_reach_h():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),)
    with pytest.raises(KeyNotFound):
        es_weighted_modulus(layers, h_m=5.0, legacy_compat=False)


@pytest.mark.unit
def test_legacy_never_raises_even_when_short_of_h():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),)
    assert legacy_weighted_modulus(layers, h_m=5.0) == pytest.approx(2.0 * 10.0 / 5.0, rel=1e-9)


@pytest.mark.unit
def test_legacy_does_not_clip_a_layer_thickness_to_h():
    """The sheet's `H11` formula has no `MIN(...)` against `h_m`: a first-4 layer extending past
    `h_m` still contributes its FULL thickness (over-counting), not just the part inside [0,h_m]."""
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=1.6, modulo_MPa=180.0), SoilLayer(z_top_m=1.6, z_bot_m=4.5, modulo_MPa=140.0))
    assert legacy_weighted_modulus(layers, h_m=3.0) == pytest.approx((180 * 1.6 + 140 * 2.9) / 3.0, rel=1e-9)

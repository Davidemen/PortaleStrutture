import pytest

from strutture.geotechnics.cedimenti_elastico.ground_to_base import shift_to_base
from strutture.shared.soil_layers import SoilLayer


@pytest.mark.unit
def test_shift_matches_centro_golden_case():
    ground = (
        SoilLayer(z_top_m=0.80, z_bot_m=4.80, modulo_MPa=5.5),
        SoilLayer(z_top_m=4.80, z_bot_m=5.80, modulo_MPa=7.0),
    )
    shifted = shift_to_base(ground, embedment_m=1.10)
    assert shifted[0].z_top_m == pytest.approx(0.0)
    assert shifted[0].z_bot_m == pytest.approx(3.70)
    assert shifted[1].z_top_m == pytest.approx(3.70)
    assert shifted[1].z_bot_m == pytest.approx(4.70)


@pytest.mark.unit
def test_layer_fully_above_embedment_is_dropped():
    ground = (SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0), SoilLayer(z_top_m=1.0, z_bot_m=3.0, modulo_MPa=20.0))
    shifted = shift_to_base(ground, embedment_m=1.0)
    assert len(shifted) == 1
    assert shifted[0].z_top_m == 0.0
    assert shifted[0].z_bot_m == pytest.approx(2.0)


@pytest.mark.unit
def test_no_embedment_is_identity_shape():
    ground = (SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0), SoilLayer(z_top_m=1.0, z_bot_m=2.0, modulo_MPa=20.0))
    shifted = shift_to_base(ground, embedment_m=0.0)
    assert shifted == ground


@pytest.mark.unit
def test_rounds_away_float_noise_at_the_boundary():
    # 4.80 - 1.10 == 3.6999999999999997 in raw float arithmetic; must land exactly on 3.7.
    shifted = shift_to_base((SoilLayer(z_top_m=0.80, z_bot_m=4.80, modulo_MPa=1.0),), embedment_m=1.10)
    assert shifted[0].z_bot_m == 3.7

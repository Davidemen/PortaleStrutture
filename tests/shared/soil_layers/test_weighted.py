"""`weighted_modulus`: generalises the T&G sheet's `H11` (hard-wired to 4 layers) to any n.

Golden reference: `build/data/geo-cedimenti/elastico-timoshenko-goodier-3.csv` rows 10-14
(from-foundation depths, kg/cmq): strato1 0-160->180, strato2 160-450->140, strato3/4 450-450
(zero-thickness, omitted here — `SoilLayer` forbids zero-thickness rows by construction), strato5
450-11950->280; H=500cm. The sheet's own `Es`=138.8 kg/cmq is the *legacy* value because its
formula only sums the first 4 (hardcoded) rows and still divides by the full H=500, silently
dropping strato5's [450,500] contribution (§7 "T-G-3 H11" bug) — the code-standard fix below
includes every layer's overlap with `[0, H]` and gets 166.8 kg/cmq (16.3559 MPa) instead."""
import pytest

from strutture.shared.soil_layers import SoilLayer, weighted_modulus
from strutture.shared.tables import KeyNotFound
from strutture.shared.units import cm_to_m, kgcm2_to_mpa

LAYERS = (
    SoilLayer(z_top_m=0.0, z_bot_m=cm_to_m(160), modulo_MPa=kgcm2_to_mpa(180.0)),
    SoilLayer(z_top_m=cm_to_m(160), z_bot_m=cm_to_m(450), modulo_MPa=kgcm2_to_mpa(140.0)),
    SoilLayer(z_top_m=cm_to_m(450), z_bot_m=cm_to_m(11950), modulo_MPa=kgcm2_to_mpa(280.0)),
)
H_M = cm_to_m(500)


@pytest.mark.unit
def test_fixed_behaviour_covers_every_layer_unlike_the_sheet() -> None:
    expected_kgcm2 = 166.8
    assert weighted_modulus(LAYERS, H_M) == pytest.approx(kgcm2_to_mpa(expected_kgcm2), rel=1e-6)


@pytest.mark.unit
def test_single_layer_returns_its_own_modulus() -> None:
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=10.0, modulo_MPa=25.0),)
    assert weighted_modulus(layers, 4.0) == pytest.approx(25.0)


@pytest.mark.unit
def test_generalizes_beyond_four_layers() -> None:
    layers = tuple(SoilLayer(z_top_m=float(i), z_bot_m=float(i + 1), modulo_MPa=float(i + 1) * 10) for i in range(6))
    # 6 layers of 1 m each, E = 10,20,...,60 MPa; weighted average over [0,6] = mean = 35 MPa.
    assert weighted_modulus(layers, 6.0) == pytest.approx(35.0)


@pytest.mark.unit
def test_raises_when_profile_does_not_cover_h() -> None:
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),)
    with pytest.raises(KeyNotFound):
        weighted_modulus(layers, 5.0)


@pytest.mark.unit
def test_rejects_non_positive_h() -> None:
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),)
    with pytest.raises(ValueError, match="h_m"):
        weighted_modulus(layers, 0.0)

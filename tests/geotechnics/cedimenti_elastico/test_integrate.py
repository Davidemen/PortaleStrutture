import pytest

from strutture.geotechnics.cedimenti_elastico.integrate import integrate_settlement, total_settlement_m
from strutture.shared.report import CalcError
from strutture.shared.soil_layers import SoilLayer


@pytest.mark.unit
def test_constant_sigma_over_one_layer():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),)
    slices = integrate_settlement((0.5, 1.0, 1.5, 2.0), layers, lambda _z: 1000.0)  # 1 MPa in kPa
    assert total_settlement_m(slices) == pytest.approx(2.0 * (1.0 / 10.0), rel=1e-12)


@pytest.mark.unit
def test_legacy_past_coverage_contributes_zero():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),)
    slices = integrate_settlement((0.5, 1.5), layers, lambda _z: 1000.0, legacy_compat=True)
    assert slices[0].modulo_MPa == 10.0
    assert slices[1].modulo_MPa is None
    assert slices[1].delta_w_m == 0.0


@pytest.mark.unit
def test_code_standard_raises_past_coverage():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),)
    with pytest.raises(CalcError):
        integrate_settlement((0.5, 1.5), layers, lambda _z: 1000.0, legacy_compat=False)


@pytest.mark.unit
def test_legacy_evaluates_sigma_at_the_slice_bottom():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=10.0, modulo_MPa=1.0),)
    seen_z_m: list[float] = []

    def sigma(z_m: float) -> float:
        seen_z_m.append(z_m)
        return 1000.0

    slices = integrate_settlement((1.0, 2.0), layers, sigma, legacy_compat=True)
    assert seen_z_m == [1.0, 2.0]
    assert [s.z_m for s in slices] == [1.0, 2.0]


@pytest.mark.unit
def test_code_standard_evaluates_sigma_at_the_slice_midpoint():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=10.0, modulo_MPa=1.0),)
    seen_z_m: list[float] = []

    def sigma(z_m: float) -> float:
        seen_z_m.append(z_m)
        return 1000.0

    slices = integrate_settlement((1.0, 2.0), layers, sigma, legacy_compat=False)
    assert seen_z_m == [0.5, 1.5]  # midpoints, not the slice bottoms
    assert [s.z_m for s in slices] == [1.0, 2.0]  # reported z_m is still the slice bottom


@pytest.mark.unit
def test_code_standard_does_not_under_predict_a_decreasing_stress_like_the_legacy_right_endpoint():
    layers = (SoilLayer(z_top_m=0.0, z_bot_m=10.0, modulo_MPa=1.0),)

    def decreasing_sigma(z_m: float) -> float:
        return 1000.0 / z_m

    grid = tuple(0.5 * i for i in range(1, 21))  # z=0.5..10.0m
    legacy_total = total_settlement_m(integrate_settlement(grid, layers, decreasing_sigma, legacy_compat=True))
    fixed_total = total_settlement_m(integrate_settlement(grid, layers, decreasing_sigma, legacy_compat=False))
    assert fixed_total > legacy_total

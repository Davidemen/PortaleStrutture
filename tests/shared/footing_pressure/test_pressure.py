"""Top-level dispatcher: metodo selection, both branches reachable, CalcError propagation."""
import pytest

from strutture.shared.footing_pressure import biaxial, pressure, sovrapposizione
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit


def test_esatto_is_the_default_and_matches_biaxial():
    n_kn, mx_knm, my_knm, bx_m, by_m = 1500.0, 300.0, 200.0, 4.0, 5.0
    default = pressure(n_kn, mx_knm, my_knm, bx_m, by_m)
    explicit = pressure(n_kn, mx_knm, my_knm, bx_m, by_m, metodo="esatto")
    direct = biaxial(n_kn, mx_knm, my_knm, bx_m, by_m)
    assert default.metodo == "esatto"
    assert default.sigma_max_kpa == pytest.approx(direct.sigma_max_kpa)
    assert explicit.sigma_max_kpa == pytest.approx(direct.sigma_max_kpa)


def test_sovrapposizione_metodo_matches_direct_call():
    n_kn, mx_knm, my_knm, bx_m, by_m = 1500.0, 900.0, 700.0, 4.0, 4.0
    result = pressure(n_kn, mx_knm, my_knm, bx_m, by_m, metodo="sovrapposizione")
    direct = sovrapposizione(n_kn, mx_knm, my_knm, bx_m, by_m)
    assert result.metodo == "sovrapposizione"
    assert result.sigma_max_kpa == pytest.approx(direct.sigma_max_kpa)


def test_unknown_metodo_rejected():
    with pytest.raises(ValueError):
        pressure(1000.0, 0.0, 0.0, 4.0, 4.0, metodo="altro")  # type: ignore[arg-type]


def test_calc_error_propagates_from_both_methods():
    n_kn, bx_m, by_m = 1000.0, 4.0, 6.0
    my_knm_outside = n_kn * 2.5  # ex=2.5 >= bx/2=2.0
    with pytest.raises(CalcError):
        pressure(n_kn, 0.0, my_knm_outside, bx_m, by_m, metodo="esatto")
    with pytest.raises(CalcError):
        pressure(n_kn, 0.0, my_knm_outside, bx_m, by_m, metodo="sovrapposizione")

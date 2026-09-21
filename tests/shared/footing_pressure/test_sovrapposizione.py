"""Sheet superposition method: docs/specs/fond-plinti-isolati.md steps 9-10 (CHECKS!AA), golden
row 6 (ULS1, node 1832). Same kg/cm2-per-kPa=100 sheet convention as test_uniaxial.py.
"""
import pytest

from strutture.shared.footing_pressure.sovrapposizione import sovrapposizione
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

_SHEET_KGCM2_PER_KPA = 1.0 / 100.0


@pytest.mark.golden
def test_matches_spec_golden_case_total_pressure():
    n_kn, mxx_knm, myy_knm, bx_m, by_m = 2596.93, 40.9685, 1.42918, 4.0, 4.0
    result = sovrapposizione(n_kn, mxx_knm, myy_knm, bx_m, by_m)
    assert result.sigma_max_kpa * _SHEET_KGCM2_PER_KPA == pytest.approx(1.66283, rel=1e-4)
    assert result.compressed_ratio == pytest.approx(1.0)  # AP = MIN(S,Z) = 1 in the golden case


def test_zero_eccentricity_matches_uniform_pressure():
    n_kn, bx_m, by_m = 1000.0, 4.0, 5.0
    result = sovrapposizione(n_kn, 0.0, 0.0, bx_m, by_m)
    uniform = n_kn / (bx_m * by_m)
    assert result.sigma_max_kpa == pytest.approx(uniform)
    assert result.sigma_min_kpa == pytest.approx(uniform)
    assert result.compressed_ratio == 1.0
    assert result.warning is None


def test_warns_only_when_both_directions_are_outside_their_own_kern():
    n_kn, bx_m, by_m = 1000.0, 4.0, 4.0  # kern half-widths bx/6=by/6=0.667
    both_outside = sovrapposizione(n_kn, n_kn * 1.0, n_kn * 1.0, bx_m, by_m)
    assert both_outside.warning is not None

    one_outside = sovrapposizione(n_kn, n_kn * 1.0, 0.0, bx_m, by_m)
    assert one_outside.warning is None

    both_inside = sovrapposizione(n_kn, n_kn * 0.1, n_kn * 0.1, bx_m, by_m)
    assert both_inside.warning is None


def test_compressed_ratio_is_min_of_the_two_axis_ratios():
    n_kn, bx_m, by_m, ex_m = 1000.0, 4.0, 4.0, 1.2  # outside kern (bx/6=0.667): contact_len = 3*(2-1.2)=2.4
    result = sovrapposizione(n_kn, 0.0, n_kn * ex_m, bx_m, by_m)
    assert result.compressed_ratio == pytest.approx(2.4 / bx_m, rel=1e-9)


def test_swap_x_and_y_gives_the_same_extremes():
    n_kn, bx_m, by_m, mx_knm, my_knm = 1500.0, 4.0, 6.0, 400.0, 250.0
    result = sovrapposizione(n_kn, mx_knm, my_knm, bx_m, by_m)
    swapped = sovrapposizione(n_kn, my_knm, mx_knm, by_m, bx_m)
    assert swapped.sigma_max_kpa == pytest.approx(result.sigma_max_kpa)
    assert swapped.sigma_min_kpa == pytest.approx(result.sigma_min_kpa)
    assert swapped.compressed_ratio == pytest.approx(result.compressed_ratio)


def test_resultant_outside_footing_raises_calc_error():
    n_kn, bx_m, by_m = 1000.0, 4.0, 6.0
    with pytest.raises(CalcError):
        sovrapposizione(n_kn, n_kn * 3.5, 0.0, bx_m, by_m)  # ey=3.5 >= by/2=3.0

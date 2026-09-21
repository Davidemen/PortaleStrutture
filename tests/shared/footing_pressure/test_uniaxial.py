"""Uniaxial closed-form contact pressure: Navier inside the kern, no-tension triangle outside it.

Golden values from docs/specs/fond-plinti-isolati.md §"Golden test case (ULS1, node 1832)": the
sheet's cached CHECKS!O..R / V..Y for row 6 are cm-kg/cm2-scaled by the sheet's own approximate
MPa->kgf/cm2 factor of 10 (not the physical 98.0665 kPa/kgf-cm2 used by shared.units) — see the
"Constants" section of the spec ("...combined into the literal factors 10..."). This module works
in exact SI kPa throughout, so the golden comparison below multiplies the spec's kg/cm2 figures by
100 (== dividing our kPa result by 100) to reproduce that same, intentionally approximate, sheet
convention rather than the exact shared.units.kpa_to_kgcm2 conversion. Flagged for the plinti_isolati
Tool layer in the footing_pressure hand-off notes.
"""
import pytest

from strutture.shared.footing_pressure.uniaxial import uniaxial
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

_SHEET_KGCM2_PER_KPA = 1.0 / 100.0  # sheet's own (approximate) MPa->kgf/cm2 factor of 10, see module docstring


@pytest.mark.golden
def test_matches_spec_golden_case_x_direction():
    # N=2596.93 kN, MYY=1.42918 kNm -> eccX=0.000550 m, AX=BY=4 m.
    result = uniaxial(n_kn=2596.93, m_knm=1.42918, b_m=4.0, l_m=4.0)
    assert result.in_kern is True
    assert result.sigma_min_kpa * _SHEET_KGCM2_PER_KPA == pytest.approx(1.62174, rel=1e-4)
    assert result.sigma_max_kpa * _SHEET_KGCM2_PER_KPA == pytest.approx(1.62442, rel=1e-4)


@pytest.mark.golden
def test_matches_spec_golden_case_y_direction():
    # MXX=40.9685 kNm -> eccY=0.015776 m.
    result = uniaxial(n_kn=2596.93, m_knm=40.9685, b_m=4.0, l_m=4.0)
    assert result.in_kern is True
    assert result.sigma_min_kpa * _SHEET_KGCM2_PER_KPA == pytest.approx(1.58467, rel=1e-4)
    assert result.sigma_max_kpa * _SHEET_KGCM2_PER_KPA == pytest.approx(1.66149, rel=1e-4)


def test_zero_eccentricity_gives_uniform_pressure():
    result = uniaxial(n_kn=1000.0, m_knm=0.0, b_m=4.0, l_m=5.0)
    assert result.in_kern is True
    assert result.sigma_max_kpa == pytest.approx(result.sigma_min_kpa)
    assert result.sigma_max_kpa == pytest.approx(1000.0 / (4.0 * 5.0))
    assert result.contact_len_m == pytest.approx(5.0)


def test_kern_boundary_e_equals_l_over_6_gives_zero_min_pressure():
    l_m = 6.0
    result = uniaxial(n_kn=600.0, m_knm=600.0 * (l_m / 6.0), b_m=3.0, l_m=l_m)
    assert result.in_kern is True
    assert result.sigma_min_kpa == pytest.approx(0.0, abs=1e-9)


def test_partial_contact_matches_closed_form_2n_over_3b_times_l_half_minus_e():
    n_kn, b_m, l_m, e_m = 800.0, 3.0, 6.0, 2.0  # e=2 > l/6=1: outside the kern
    result = uniaxial(n_kn=n_kn, m_knm=n_kn * e_m, b_m=b_m, l_m=l_m)
    assert result.in_kern is False
    expected_sigma_max = 2.0 * n_kn / (3.0 * b_m * (l_m / 2.0 - e_m))
    assert result.sigma_max_kpa == pytest.approx(expected_sigma_max, rel=1e-9)
    assert result.sigma_min_kpa == 0.0
    assert result.contact_len_m == pytest.approx(3.0 * (l_m / 2.0 - e_m))


def test_monotonic_sigma_max_as_eccentricity_grows():
    n_kn, b_m, l_m = 1000.0, 4.0, 6.0
    sigmas = [uniaxial(n_kn, n_kn * e, b_m, l_m).sigma_max_kpa for e in (0.0, 0.5, 1.0, 1.5, 2.0, 2.4, 2.9)]
    assert sigmas == sorted(sigmas)


def test_negative_eccentricity_mirrors_positive():
    n_kn, b_m, l_m, e_m = 1000.0, 4.0, 6.0, 1.5
    positive = uniaxial(n_kn, n_kn * e_m, b_m, l_m)
    negative = uniaxial(n_kn, -n_kn * e_m, b_m, l_m)
    assert negative.sigma_max_kpa == pytest.approx(positive.sigma_max_kpa)
    assert negative.sigma_min_kpa == pytest.approx(positive.sigma_min_kpa)


def test_resultant_outside_footing_raises_calc_error():
    with pytest.raises(CalcError):
        uniaxial(n_kn=1000.0, m_knm=1000.0 * 3.5, b_m=4.0, l_m=6.0)  # e=3.5 >= l/2=3.0


@pytest.mark.parametrize(("n_kn", "b_m", "l_m"), [(0.0, 4.0, 6.0), (-1.0, 4.0, 6.0), (1000.0, 0.0, 6.0),
                                                   (1000.0, 4.0, 0.0)])
def test_rejects_invalid_geometry(n_kn, b_m, l_m):
    with pytest.raises(ValueError):
        uniaxial(n_kn=n_kn, m_knm=0.0, b_m=b_m, l_m=l_m)

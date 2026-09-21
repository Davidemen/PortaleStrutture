"""m exponent, iq/iγ/ic load-inclination factors (EN 1997-1 Annex D.2/D.3)."""
import math

import pytest

from strutture.shared.capacita_portante.fattori_inclinazione import (
    esponente_m,
    fattori_inclinazione_carico,
    fattori_inclinazione_carico_non_drenata,
)
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit


def test_m_b_direction_hand_computed():
    # B'=2, L'=4 -> B'/L'=0.5: mB = (2+0.5)/(1+0.5) = 5/3.
    assert esponente_m(2.0, 4.0, direzione="B") == pytest.approx(5.0 / 3.0)


def test_m_l_direction_hand_computed():
    # L'/B'=2: mL = (2+2)/(1+2) = 4/3.
    assert esponente_m(2.0, 4.0, direzione="L") == pytest.approx(4.0 / 3.0)


def test_m_theta_combines_mb_and_ml():
    mb = esponente_m(2.0, 4.0, direzione="B")
    ml = esponente_m(2.0, 4.0, direzione="L")
    theta_rad = math.radians(30.0)
    atteso = ml * math.cos(theta_rad) ** 2 + mb * math.sin(theta_rad) ** 2
    assert esponente_m(2.0, 4.0, direzione="theta", theta_deg=30.0) == pytest.approx(atteso)


def test_m_theta_zero_equals_ml_and_ninety_equals_mb():
    ml = esponente_m(2.0, 4.0, direzione="L")
    mb = esponente_m(2.0, 4.0, direzione="B")
    assert esponente_m(2.0, 4.0, direzione="theta", theta_deg=0.0) == pytest.approx(ml)
    assert esponente_m(2.0, 4.0, direzione="theta", theta_deg=90.0) == pytest.approx(mb, abs=1e-9)


def test_strip_footing_m_limits():
    assert esponente_m(2.0, math.inf, direzione="B") == pytest.approx(2.0)
    assert esponente_m(2.0, math.inf, direzione="L") == pytest.approx(1.0)


def test_zero_horizontal_load_gives_unit_factors():
    fattori = fattori_inclinazione_carico(0.0, 1000.0, 6.0, 0.0, 30.0, 30.14, m=1.5)
    assert fattori.iq == pytest.approx(1.0)
    assert fattori.igamma == pytest.approx(1.0)
    assert fattori.ic == pytest.approx(1.0)


def test_hand_computed_inclination_c_zero():
    # H=200, V=1000, A'=6, c'=0 -> base = 1 - H/V = 0.8; m=1.5.
    fattori = fattori_inclinazione_carico(200.0, 1000.0, 6.0, 0.0, 30.0, 30.14, m=1.5)
    assert fattori.iq == pytest.approx(0.8**1.5)
    assert fattori.igamma == pytest.approx(0.8**2.5)


def test_inclination_factors_decrease_monotonically_with_h():
    valori = [fattori_inclinazione_carico(h, 1000.0, 6.0, 0.0, 30.0, 30.14, m=1.5).iq for h in (0.0, 100.0, 200.0, 300.0)]
    assert valori == sorted(valori, reverse=True)


def test_h_exceeding_available_friction_raises_calc_error():
    with pytest.raises(CalcError):
        fattori_inclinazione_carico(1500.0, 1000.0, 6.0, 0.0, 30.0, 30.14, m=1.5)


def test_phi_zero_drained_formula_raises_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_carico(10.0, 1000.0, 6.0, 0.0, 0.0, 30.14, m=1.5)


def test_undrained_ic_hand_computed():
    # ic = 0.5*(1 + sqrt(1 - H/(A'*cu))); H=100, A'=6, cu=50 -> A'cu=300.
    ic = fattori_inclinazione_carico_non_drenata(h_kn=100.0, a_eff_m2=6.0, cu_kpa=50.0)
    assert ic == pytest.approx(0.5 * (1.0 + math.sqrt(1.0 - 100.0 / 300.0)))


def test_undrained_h_at_limit_gives_ic_one_half():
    ic = fattori_inclinazione_carico_non_drenata(h_kn=300.0, a_eff_m2=6.0, cu_kpa=50.0)
    assert ic == pytest.approx(0.5)


def test_undrained_h_exceeding_a_eff_cu_raises_calc_error():
    with pytest.raises(CalcError):
        fattori_inclinazione_carico_non_drenata(h_kn=400.0, a_eff_m2=6.0, cu_kpa=50.0)


def test_esponente_m_invalid_dimensions_raise_value_error():
    with pytest.raises(ValueError):
        esponente_m(0.0, 3.0)


def test_inclinazione_carico_negative_h_or_v_raise_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_carico(-1.0, 1000.0, 6.0, 0.0, 30.0, 30.14, m=1.5)


def test_inclinazione_carico_non_drenata_negative_h_raises_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_carico_non_drenata(h_kn=-1.0, a_eff_m2=6.0, cu_kpa=50.0)


def test_ic_is_clamped_at_zero_instead_of_raising_a_validation_error():
    """MEDIUM finding: phi'=25 deg, c'=20 kPa, A'=6 m^2, V=500 kN, H=600 kN, m=1.6 (e.g. mB of a
    2x3 footing: (2+2/3)/(1+2/3)=1.6). Nq = e^(pi*tan25)*tan^2(45+12.5) = 10.662142 (Annex D.4).
    Nc = (Nq-1)/tan(25 deg) = 20.720531. denom = V + A'*c'*cot(phi') = 500 + 120/tan(25 deg)
       = 757.340830 kN. base = 1 - 600/757.340830 = 0.207754. iq = base**1.6 = 0.080925.
    ic = iq - (1-iq)/(Nc*tan(phi')) = 0.080925 - 0.919075/(20.720531*0.466308) = -0.014197 < 0
       -> Annex D's c' term physically cannot subtract more than it adds, so the module must
    clamp ic at 0.0 rather than let pydantic's `ic (ge=0)` constraint raise a ValidationError."""
    fattori = fattori_inclinazione_carico(h_kn=600.0, v_kn=500.0, a_eff_m2=6.0, c_kpa=20.0, phi_deg=25.0, nc=20.720531, m=1.6)
    assert fattori.ic == pytest.approx(0.0)

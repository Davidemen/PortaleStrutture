import pytest

from strutture.members.ca_fessurazione.spaziatura_fessure import (
    delta_sm_c4_1_7_mm,
    delta_sm_c4_1_10_mm,
    delta_sm_effettivo_mm,
    ramo_spaziatura,
    spaziatura_limite_mm,
)

pytestmark = pytest.mark.unit


def test_spaziatura_limite():
    assert spaziatura_limite_mm(copriferro_mm=35, phi_eq_mm=20) == pytest.approx(225, rel=1e-9)


def test_delta_sm_c4_1_7():
    result = delta_sm_c4_1_7_mm(k3=3.4, copriferro_mm=35, k1=0.8, k2=0.5, k4=0.425, phi_eq_mm=20, rho_eff=0.0270578145405644)
    assert result == pytest.approx(143.916, rel=1e-5)


def test_delta_sm_c4_1_7_rejects_non_positive_rho():
    with pytest.raises(ValueError, match="rho_eff"):
        delta_sm_c4_1_7_mm(k3=3.4, copriferro_mm=35, k1=0.8, k2=0.5, k4=0.425, phi_eq_mm=20, rho_eff=0)


def test_delta_sm_c4_1_10_legacy_uses_sheet_factor_0_75():
    assert delta_sm_c4_1_10_mm(h_mm=250, x_mm=75.84, legacy_compat=True) == pytest.approx(130.62, rel=1e-9)


def test_delta_sm_c4_1_10_fixed_uses_1_3_over_1_7_per_en1992_eq_7_14():
    """EN1992-1-1 eq. 7.14 / Circ. 2019 §C4.1.10: sr,max = 1.3*(h-x), i.e. k = 1.3/1.7 once
    wk = 1.7*epsilon_sm*delta_sm is applied — see docs/divergences/ca-fessurazione.md."""
    result = delta_sm_c4_1_10_mm(h_mm=250, x_mm=75.84, legacy_compat=False)
    assert result == pytest.approx((1.3 / 1.7) * (250 - 75.84), rel=1e-9)
    assert result > 130.62  # ~2% larger (less conservative sheet value under legacy_compat=True)


@pytest.mark.parametrize(("interferro_mm", "slim_mm", "atteso"), [(200, 225, "C4.1.7"), (500, 186.67, "C4.1.10"), (225, 225, "C4.1.10")])
def test_ramo_spaziatura(interferro_mm, slim_mm, atteso):
    assert ramo_spaziatura(interferro_mm, slim_mm) == atteso


def test_delta_sm_effettivo_selects_branch():
    assert delta_sm_effettivo_mm("C4.1.7", delta_c4_1_7_mm=143.9, delta_c4_1_10_mm=130.6) == pytest.approx(143.9, rel=1e-9)
    assert delta_sm_effettivo_mm("C4.1.10", delta_c4_1_7_mm=143.9, delta_c4_1_10_mm=130.6) == pytest.approx(130.6, rel=1e-9)

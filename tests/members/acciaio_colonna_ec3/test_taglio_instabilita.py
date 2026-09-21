"""taglio_instabilita.py — shear buckling of the web (column-check!AC27-O75, EN1993-1-5 §5)."""
import pytest

from strutture.members.acciaio_colonna_ec3.taglio_instabilita import (
    costruisci_taglio_instabilita,
    epsilon,
    eta,
    hw_su_t,
    limite_hw_t,
    richiede_verifica_taglio,
)


@pytest.mark.unit
def test_hw_su_t() -> None:
    assert hw_su_t(500, 12, 8) == pytest.approx((500 - 24) / 8)


@pytest.mark.unit
def test_epsilon_and_eta() -> None:
    assert epsilon(345) == pytest.approx((235.0 / 345.0) ** 0.5)
    assert eta(345) == 1.2
    assert eta(500) == 1.0


@pytest.mark.unit
def test_limite_72_eps_eta_golden_legacy() -> None:
    """Legacy reproduces the sheet's 72*eps*eta (AD27)."""
    assert limite_hw_t(epsilon(345), eta(345), legacy_compat=True) == pytest.approx(71.308, rel=1e-4)


@pytest.mark.unit
def test_limite_72_eps_su_eta_fixed() -> None:
    """EN1993-1-5 §5.1(2) divides by eta, not multiplies."""
    eps, et = epsilon(345), eta(345)
    fixed = limite_hw_t(eps, et, legacy_compat=False)
    assert fixed == pytest.approx(72.0 * eps / et)
    assert fixed != pytest.approx(limite_hw_t(eps, et, legacy_compat=True))


@pytest.mark.unit
def test_richiede_verifica_is_inverted_between_modes() -> None:
    """Legacy reproduces `hw_t <= limite` (K32); EN1993-1-5 §5.1(2) requires `hw_t > limite`."""
    assert richiede_verifica_taglio(60.0, 70.0, legacy_compat=True) is True
    assert richiede_verifica_taglio(60.0, 70.0, legacy_compat=False) is False
    assert richiede_verifica_taglio(80.0, 70.0, legacy_compat=True) is False
    assert richiede_verifica_taglio(80.0, 70.0, legacy_compat=False) is True


@pytest.mark.unit
def test_costruisci_taglio_instabilita_golden() -> None:
    result = costruisci_taglio_instabilita(
        b_mm=280, h_mm=500, tw_mm=8, tf_mm=12, ly_mm=18850, fyd_MPa=345, fyk_MPa=345, gamma_m0=1.0, gamma_m1=1.0,
        nsd_kN=172.326, my_sd_kNm=120.689, vy_sd_kN=29.2057, legacy_compat=True,
    )
    assert result.hw_t == pytest.approx(59.5)
    assert result.richiede_verifica is True  # hw/t (59.5) <= limit (71.3): legacy flag (K32) set
    assert result.vb_rd_kN == pytest.approx(757.091, rel=1e-4)
    assert result.verifica.passed is True


@pytest.mark.unit
def test_thin_web_does_not_require_the_check_legacy() -> None:
    result = costruisci_taglio_instabilita(
        b_mm=280, h_mm=500, tw_mm=4, tf_mm=12, ly_mm=18850, fyd_MPa=345, fyk_MPa=345, gamma_m0=1.0, gamma_m1=1.0,
        nsd_kN=172.326, my_sd_kNm=120.689, vy_sd_kN=29.2057, legacy_compat=True,
    )
    assert result.richiede_verifica is False


@pytest.mark.unit
def test_fixed_mode_uses_fyk_and_correct_hw_t_direction() -> None:
    """At gammaM0=1.05 (fyk != fyd), fixed mode uses fyk for eps/eta and requires hw_t > limite."""
    fyk, fyd = 345.0, 345.0 / 1.05
    legacy = costruisci_taglio_instabilita(
        b_mm=280, h_mm=500, tw_mm=8, tf_mm=12, ly_mm=18850, fyd_MPa=fyd, fyk_MPa=fyk, gamma_m0=1.05, gamma_m1=1.05,
        nsd_kN=172.326, my_sd_kNm=120.689, vy_sd_kN=29.2057, legacy_compat=True,
    )
    fixed = costruisci_taglio_instabilita(
        b_mm=280, h_mm=500, tw_mm=8, tf_mm=12, ly_mm=18850, fyd_MPa=fyd, fyk_MPa=fyk, gamma_m0=1.05, gamma_m1=1.05,
        nsd_kN=172.326, my_sd_kNm=120.689, vy_sd_kN=29.2057, legacy_compat=False,
    )
    assert fixed.limite_72_eps_eta != pytest.approx(legacy.limite_72_eps_eta)
    assert fixed.limite_72_eps_eta == pytest.approx(72.0 * (235.0 / fyk) ** 0.5 / 1.2)
    assert legacy.richiede_verifica is True
    assert fixed.richiede_verifica is True  # hw/t=59.5 > fixed limite=49.5 -> check required (§5.1(2))

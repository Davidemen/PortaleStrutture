"""instabilita_flesso_torsionale.py — LTB (column-check!AI8, S34, W36, U37, O59).

New divergence: U37 (chi_LT) omits phi_LT^2 from the sqrt radicand — see module docstring.
"""
import math

import pytest

from strutture.members.acciaio_colonna_ec3.instabilita_flesso_torsionale import (
    costruisci_ltb,
    fattore_chi_lt,
    fattore_phi_lt,
    ltb_non_necessaria,
    momento_critico_Nmm,
    snellezza_lt,
)


@pytest.mark.unit
def test_momento_critico_golden() -> None:
    mcr = momento_critico_Nmm(c1=1.871, e_MPa=206000.0, izz_mm4=4.39243e7, lt_mm=1800.0, iw_mm6=2.6151e12, g_MPa=79230.8, it_mm4=4.05255e5)
    assert mcr == pytest.approx(1.27057e10, rel=1e-4)


@pytest.mark.unit
def test_snellezza_lt_uses_wpl_for_class_1_2_and_wel_for_3_4() -> None:
    mcr = 1.27057e10
    assert snellezza_lt(1, 1.88825e6, 2.09283e6, 345, mcr) == pytest.approx(math.sqrt(2.09283e6 * 345 / mcr))
    assert snellezza_lt(3, 1.88825e6, 2.09283e6, 345, mcr) == pytest.approx(math.sqrt(1.88825e6 * 345 / mcr))


@pytest.mark.unit
def test_legacy_chi_lt_omits_phi_squared_bug() -> None:
    """legacy_compat=True reproduces column-check!U37's missing phi_LT^2 term."""
    phi_lt = fattore_phi_lt(0.34, 0.5)
    legacy = fattore_chi_lt(phi_lt, 0.5, legacy_compat=True)
    atteso_legacy = min(1.0 / (phi_lt + math.sqrt(0.5**2 * (1.0 - 0.75))), 1.0, 1.0 / 0.5**2)
    assert legacy == pytest.approx(atteso_legacy)


@pytest.mark.unit
def test_fixed_chi_lt_uses_the_standard_ec3_formula() -> None:
    phi_lt = fattore_phi_lt(0.34, 0.5)
    fixed = fattore_chi_lt(phi_lt, 0.5, legacy_compat=False)
    atteso_fixed = min(1.0 / (phi_lt + math.sqrt(phi_lt**2 - 0.75 * 0.5**2)), 1.0, 1.0 / 0.5**2)
    assert fixed == pytest.approx(atteso_fixed)
    assert fixed != pytest.approx(fattore_chi_lt(phi_lt, 0.5, legacy_compat=True))


@pytest.mark.unit
def test_ltb_non_necessaria_boundary() -> None:
    assert ltb_non_necessaria(my_sd_kNm=1.0, mz_sd_kNm=0.0, mcr_Nmm=1e12, lambda_lt=0.1) is True
    assert ltb_non_necessaria(my_sd_kNm=500.0, mz_sd_kNm=0.0, mcr_Nmm=1e9, lambda_lt=1.0) is False


@pytest.mark.unit
def test_fixed_mode_uses_fyk_not_fyd_for_lambda_lt() -> None:
    """EN1993-1-1 eq. (6.56): lambda_bar_LT = sqrt(Wy*fy/Mcr) on the characteristic fy."""
    fyk, fyd = 345.0, 345.0 / 1.05
    kwargs = {
        "c1": 1.871, "e_MPa": 206000.0, "izz_mm4": 4.39243e7, "lt_mm": 1800.0, "iw_mm6": 2.6151e12, "g_MPa": 79230.8,
        "it_mm4": 4.05255e5, "classe_num": 3, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6, "fyd_MPa": fyd, "fyk_MPa": fyk,
        "alpha_lt": 0.34, "my_sd_kNm": 120.689, "mz_sd_kNm": 0.00639699,
    }
    legacy = costruisci_ltb(**kwargs, legacy_compat=True)
    fixed = costruisci_ltb(**kwargs, legacy_compat=False)
    assert legacy.lambda_lt == pytest.approx(snellezza_lt(3, 1.88825e6, 2.09283e6, fyd, legacy.mcr_Nmm))
    assert fixed.lambda_lt == pytest.approx(snellezza_lt(3, 1.88825e6, 2.09283e6, fyk, fixed.mcr_Nmm))
    assert fixed.lambda_lt > legacy.lambda_lt

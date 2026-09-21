"""annex_a_cm.py — Cmy, Cmz, CmLT (EN1993-1-1 Annex A/Table B.3; column-check!AI35-AM66).

New divergence: Cmz's diagram-type-2 branch (AN53) reuses Iyy instead of Izz — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.annex_a_cm import (
    cm0_tipo1,
    cm0_tipo3a,
    cm0_tipo3b,
    cm_lt,
    cmy,
    cmz,
    epsilon_y,
    rapporto_estremi,
    soglia_lambda0,
)


@pytest.mark.unit
def test_rapporto_estremi() -> None:
    assert rapporto_estremi(120.689, 0.00695734) == pytest.approx(0.00695734 / 120.689)


@pytest.mark.unit
def test_cm0_tipo1_end_moments() -> None:
    psi = 0.00695734 / 120.689
    assert cm0_tipo1(psi, 172.326, 3531.51) == pytest.approx(0.79 + 0.21 * psi + 0.36 * (psi - 0.33) * 172.326 / 3531.51)


@pytest.mark.unit
def test_cm0_tipo3a_and_3b() -> None:
    assert cm0_tipo3a(172.326, 3531.51) == pytest.approx(1.0 - 0.18 * 172.326 / 3531.51)
    assert cm0_tipo3b(172.326, 3531.51) == pytest.approx(1.0 + 0.03 * 172.326 / 3531.51)


@pytest.mark.unit
def test_cmy_type1_matches_golden_case() -> None:
    valore = cmy(
        "1", lambda_lt=0.226433, soglia_lambda0=0.272651, my_sd_kNm=120.689, mj_y_kNm=0.00695734,
        e_MPa=206000, iyy_mm4=4.72063e8, dmax_yy_mm=0, lcr_yy_mm=16485.6, nsd_kN=172.326, ncr_y_kN=3531.51,
        alpha_lt_torsione=0.999142, eps_y=3.90484,
    )
    assert valore == pytest.approx(0.784216, rel=1e-4)


@pytest.mark.unit
def test_cmz_type2_legacy_uses_iyy_bug() -> None:
    legacy = cmz(
        "2", mz_sd_kNm=15.0, mj_z_kNm=5.0, e_MPa=206000, iyy_mm4=4.72063e8, izz_mm4=4.39243e7,
        dmax_zz_mm=30, lcr_zz_mm=2083.1, nsd_kN=172.326, ncr_z_kN=20580.29, legacy_compat=True,
    )
    fixed = cmz(
        "2", mz_sd_kNm=15.0, mj_z_kNm=5.0, e_MPa=206000, iyy_mm4=4.72063e8, izz_mm4=4.39243e7,
        dmax_zz_mm=30, lcr_zz_mm=2083.1, nsd_kN=172.326, ncr_z_kN=20580.29, legacy_compat=False,
    )
    assert legacy != pytest.approx(fixed)
    assert legacy == pytest.approx(4.69566876537158, rel=1e-4)  # cellmap oracle value for this exact case


@pytest.mark.unit
def test_cmz_type1_and_3_do_not_depend_on_iyy_izz() -> None:
    a = cmz("1", 0.00639699, 0.0224413, 206000, 1.0, 1.0, 0, 2083.1, 172.326, 20580.29, legacy_compat=True)
    b = cmz("1", 0.00639699, 0.0224413, 206000, 999.0, 1.0, 0, 2083.1, 172.326, 20580.29, legacy_compat=True)
    assert a == b


@pytest.mark.unit
def test_cmy_type3a_squared_correction_above_threshold() -> None:
    """AJ56's correction squares (1-Cmy0), unlike AJ47/AJ53/AJ59's linear form — column-check!AJ56."""
    base = cm0_tipo3a(172.326, 3531.51)
    fattore = 0.999142 * (3.90484**0.5)
    correzione = fattore / (1.0 + fattore)
    atteso = base + (1.0 - base) * (1.0 - base) * correzione
    valore = cmy(
        "3a", lambda_lt=0.5, soglia_lambda0=0.2, my_sd_kNm=120.689, mj_y_kNm=0.00695734,
        e_MPa=206000, iyy_mm4=4.72063e8, dmax_yy_mm=0, lcr_yy_mm=16485.6, nsd_kN=172.326, ncr_y_kN=3531.51,
        alpha_lt_torsione=0.999142, eps_y=3.90484,
    )
    assert valore == pytest.approx(atteso)


@pytest.mark.unit
def test_soglia_lambda0() -> None:
    valore = soglia_lambda0(1.871, 172.326, 20580.2, 34315.3)
    assert valore == pytest.approx(0.272651, rel=1e-4)


@pytest.mark.unit
def test_epsilon_y() -> None:
    assert epsilon_y(120.689, 10528, 172.326, 1.88825e6) == pytest.approx(3.90484, rel=1e-4)


@pytest.mark.unit
def test_cm_lt_returns_one_below_threshold() -> None:
    assert cm_lt(lambda_lt=0.1, soglia=0.4, cmy_valore=0.8, alpha_lt_torsione=1.0, nsd_kN=100, ncr_z_kN=1000, ncr_t_kN=1000) == 1.0

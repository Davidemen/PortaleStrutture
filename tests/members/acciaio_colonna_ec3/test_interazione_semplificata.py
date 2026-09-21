"""interazione_semplificata.py — simplified fallback checks (column-check!H46-H52, J53/J54, V54, I56).

New divergence: V54's axial term is mis-scaled by ~1000x — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.interazione_semplificata import (
    costruisci_interazione_semplificata,
    fattore_area_ali,
    fattore_area_anima,
    i56_potenza,
    mn_rd_kNm,
    mn_rd_z_kNm_fixed,
    rapporto_assiale,
)


@pytest.mark.unit
def test_rapporto_assiale_golden() -> None:
    assert rapporto_assiale(172.326, 10528, 345) == pytest.approx(0.0474445, rel=1e-4)


@pytest.mark.unit
def test_fattore_area_capped_at_0_5() -> None:
    assert fattore_area_ali(10528, 280, 12) == pytest.approx(0.361702, rel=1e-4)
    assert fattore_area_anima(10528, 500, 8) == pytest.approx(0.240122, rel=1e-4)
    assert fattore_area_ali(1000, 10, 1) == 0.5  # (1000-20)/1000=0.98, capped


@pytest.mark.unit
def test_mn_rd_capped_at_mpl() -> None:
    assert mn_rd_kNm(100.0, n=0.0, a=0.3) == pytest.approx(100.0)  # n=0 -> uncapped branch = Mpl
    assert mn_rd_kNm(100.0, n=0.9, a=0.3) < 100.0


@pytest.mark.unit
def test_i56_golden() -> None:
    n = 0.0474445
    valore = i56_potenza(120.689, 651.446, 0.00639699, 108.242, n)
    assert valore == pytest.approx(0.0343815, rel=1e-3)


@pytest.mark.unit
def test_mn_rd_z_kNm_fixed_uses_the_clause_expression() -> None:
    """EN1993-1-1 §6.2.9.1(5): MN,z,Rd = Mpl,z for n<=a, else Mpl,z*(1-((n-a)/(1-a))^2)."""
    assert mn_rd_z_kNm_fixed(100.0, n=0.2, a=0.35) == pytest.approx(100.0)  # n <= a
    atteso = 100.0 * (1.0 - ((0.5 - 0.35) / (1.0 - 0.35)) ** 2)
    assert mn_rd_z_kNm_fixed(100.0, n=0.5, a=0.35) == pytest.approx(atteso)


@pytest.mark.unit
def test_i56_fixed_uses_mn_rd_not_mpl() -> None:
    """EN1993-1-1 §6.2.9.1(6) eq. 6.41: denominators are the axial-reduced MN,Rd, not Mpl,Rd."""
    legacy = costruisci_interazione_semplificata(
        nsd_kN=800.0, area_mm2=10528, fyd_MPa=345, b_mm=280, h_mm=500, tw_mm=8, tf_mm=12,
        mpl_y_kNm=651.446, mpl_z_kNm=108.242, my_sd_kNm=300.0, mz_sd_kNm=20.0, legacy_compat=True,
    )
    fixed = costruisci_interazione_semplificata(
        nsd_kN=800.0, area_mm2=10528, fyd_MPa=345, b_mm=280, h_mm=500, tw_mm=8, tf_mm=12,
        mpl_y_kNm=651.446, mpl_z_kNm=108.242, my_sd_kNm=300.0, mz_sd_kNm=20.0, legacy_compat=False,
    )
    assert fixed.i56 > legacy.i56  # MN,Rd <= Mpl,Rd -> fixed denominators are smaller -> higher utilisation


@pytest.mark.unit
def test_fattore_area_ali_used_for_both_axes_in_fixed_mode() -> None:
    """§6.2.9.1(5) uses ONE a = MIN((A-2*b*tf)/A, 0.5) for both axes; legacy keeps H50's a_zz."""
    fixed = costruisci_interazione_semplificata(
        nsd_kN=172.326, area_mm2=10528, fyd_MPa=345, b_mm=280, h_mm=500, tw_mm=8, tf_mm=12,
        mpl_y_kNm=651.446, mpl_z_kNm=108.242, my_sd_kNm=120.689, mz_sd_kNm=0.00639699, legacy_compat=False,
    )
    a_yy = fattore_area_ali(10528, 280, 12)
    n = rapporto_assiale(172.326, 10528, 345)
    assert fixed.mn_rd_z_kNm == pytest.approx(mn_rd_z_kNm_fixed(108.242, n, a_yy))


@pytest.mark.unit
def test_v54_legacy_mis_scaled_axial_term() -> None:
    legacy = costruisci_interazione_semplificata(
        nsd_kN=172.326, area_mm2=10528, fyd_MPa=345, b_mm=280, h_mm=500, tw_mm=8, tf_mm=12,
        mpl_y_kNm=651.446, mpl_z_kNm=108.242, my_sd_kNm=120.689, mz_sd_kNm=0.00639699, legacy_compat=True,
    )
    fixed = costruisci_interazione_semplificata(
        nsd_kN=172.326, area_mm2=10528, fyd_MPa=345, b_mm=280, h_mm=500, tw_mm=8, tf_mm=12,
        mpl_y_kNm=651.446, mpl_z_kNm=108.242, my_sd_kNm=120.689, mz_sd_kNm=0.00639699, legacy_compat=False,
    )
    assert legacy.v54 == pytest.approx(0.18537, rel=1e-4)
    assert fixed.v54 > legacy.v54  # fixed restores the full n=Nsd/Npl axial contribution
    assert fixed.n_ratio == legacy.n_ratio  # H46 itself (n_ratio) is unaffected either way

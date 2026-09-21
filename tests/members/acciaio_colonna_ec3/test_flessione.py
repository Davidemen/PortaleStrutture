"""flessione.py — bending resistance with high-shear reduction (column-check!G31/G41, D33/D43).

New divergence: D33 (MRd,y) divides by gammaM0 twice; D43 (MRd,z) does not — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.flessione import costruisci_flessione, fy_ridotta_MPa, mrd_y_kNm, mrd_z_kNm


@pytest.mark.unit
def test_fy_ridotta_unreduced_below_half_capacity() -> None:
    assert fy_ridotta_MPa(taglio_condizione_kN=10, taglio_riduzione_kN=10, vpl_rd_kN=100, fyd_MPa=345) == 345


@pytest.mark.unit
def test_fy_ridotta_reduced_above_half_capacity() -> None:
    valore = fy_ridotta_MPa(taglio_condizione_kN=80, taglio_riduzione_kN=80, vpl_rd_kN=100, fyd_MPa=345)
    assert valore == pytest.approx((1.0 - (2.0 * 80 / 100 - 1.0) ** 2) * 345)
    assert valore < 345


@pytest.mark.unit
def test_mrd_y_legacy_double_divides_by_gamma_m0() -> None:
    legacy = mrd_y_kNm(3, 100.0, 200.0, 345.0, 1.05, legacy_compat=True)
    assert legacy == pytest.approx(100.0 * 345.0 / 1e6 / 1.05)


@pytest.mark.unit
def test_mrd_y_fixed_divides_once() -> None:
    fixed = mrd_y_kNm(3, 100.0, 200.0, 345.0, 1.05, legacy_compat=False)
    assert fixed == pytest.approx(100.0 * 345.0 / 1e6)
    assert fixed > mrd_y_kNm(3, 100.0, 200.0, 345.0, 1.05, legacy_compat=True)


@pytest.mark.unit
def test_mrd_z_never_double_divides() -> None:
    assert mrd_z_kNm(3, 100.0, 200.0, 345.0) == pytest.approx(100.0 * 345.0 / 1e6)


@pytest.mark.unit
def test_legacy_mode_swaps_trigger_and_reduction_axis() -> None:
    """Legacy reproduces the sheet's swap: MRd,y's trigger reads Vz,sd while its reduction uses
    Vy,sd (mirrored for MRd,z) — same swap as the pre-existing J26/J36 fix in taglio.py."""
    result = costruisci_flessione(
        classe_num=3, wel_y_mm3=1.88825e6, wpl_y_mm3=2.09283e6, wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5,
        fyd_MPa=345.0, gamma_m0=1.0, vy_sd_kN=800.0, vz_sd_kN=0.0, vpl_rd_anima_kN=1000.0,
        vpl_rd_ali_kN=1000.0, my_sd_kNm=1.0, mz_sd_kNm=1.0, legacy_compat=True,
    )
    # Vy,sd=800 > 0.5*Vpl,Rd,web=500, but the trigger reads Vz,sd=0 -> no reduction is applied at all.
    assert result.fy_ridotta_y_MPa == pytest.approx(345.0)


@pytest.mark.unit
def test_fixed_mode_uses_the_same_axis_for_trigger_and_reduction() -> None:
    """EN1993-1-1 §6.2.8(3): the trigger and rho must use the SAME VEd/Vpl,Rd per axis."""
    result = costruisci_flessione(
        classe_num=3, wel_y_mm3=1.88825e6, wpl_y_mm3=2.09283e6, wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5,
        fyd_MPa=345.0, gamma_m0=1.0, vy_sd_kN=800.0, vz_sd_kN=0.0, vpl_rd_anima_kN=1000.0,
        vpl_rd_ali_kN=1000.0, my_sd_kNm=1.0, mz_sd_kNm=1.0, legacy_compat=False,
    )
    # Vy,sd=800 > 0.5*Vpl,Rd,web=500 -> MRd,y IS reduced now that trigger and reduction share the axis.
    assert result.fy_ridotta_y_MPa < 345.0
    assert result.fy_ridotta_y_MPa == pytest.approx((1.0 - (2.0 * 800 / 1000 - 1.0) ** 2) * 345.0)
    # Vz,sd=0 -> MRd,z untouched.
    assert result.fy_ridotta_z_MPa == pytest.approx(345.0)


@pytest.mark.unit
def test_costruisci_flessione_golden() -> None:
    result = costruisci_flessione(
        classe_num=3, wel_y_mm3=1.88825e6, wpl_y_mm3=2.09283e6, wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5,
        fyd_MPa=345.0, gamma_m0=1.0, vy_sd_kN=29.2057, vz_sd_kN=0.00235166, vpl_rd_anima_kN=910.2,
        vpl_rd_ali_kN=1338.53, my_sd_kNm=120.689, mz_sd_kNm=0.00639699, legacy_compat=True,
    )
    assert result.mrd_y_kNm == pytest.approx(651.446, rel=1e-4)
    assert result.mrd_z_kNm == pytest.approx(108.242, rel=1e-4)
    assert result.verifica_y.passed is True
    assert result.verifica_z.passed is True

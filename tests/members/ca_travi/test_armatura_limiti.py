import pytest

from strutture.members.ca_travi.armatura_limiti import (
    area_minima_tesa_mm2,
    armatura_minima_massima,
    duttilita_longitudinale_sismica,
    limiti_staffe,
)

B_MM, D_MM, Z_MM = 600.0, 330.0, 297.0
FCK_MPA, FCTM_MPA, FYK_MPA, FTK_MPA = 35.0, 3.2107, 500.0, 650.0


@pytest.mark.unit
def test_as_min_legacy_uses_z_and_ftk():
    """Divergence: sheet Z12 uses z (not d) and ftk (Z7, not fyk) in the 0.26*fctm/fyk term."""
    legacy = area_minima_tesa_mm2(
        b_mm=B_MM, d_mm=D_MM, z_mm=Z_MM, fctm_MPa=3.35208, fyk_MPa=FYK_MPA, ftk_MPa=FTK_MPA, legacy_compat=True
    )
    assert legacy == pytest.approx(238.937, rel=1e-4)


@pytest.mark.unit
def test_as_min_fixed_uses_d_and_fyk_ntc2018_4_1_6_1_1():
    fixed = area_minima_tesa_mm2(
        b_mm=B_MM, d_mm=D_MM, z_mm=Z_MM, fctm_MPa=FCTM_MPA, fyk_MPa=FYK_MPA, ftk_MPa=FTK_MPA, legacy_compat=False
    )
    assert fixed == pytest.approx(max(0.0013 * B_MM * D_MM, 0.26 * B_MM * D_MM * FCTM_MPA / FYK_MPA), rel=1e-6)
    assert fixed == pytest.approx(330.498, rel=1e-3)


@pytest.mark.unit
def test_limiti_staffe_legacy_reproduces_sheet_constants():
    ast_min, passo_max = limiti_staffe(b_mm=B_MM, d_mm=D_MM, z_mm=Z_MM, fck_MPa=FCK_MPA, fyk_MPa=FYK_MPA, legacy_compat=True)
    assert ast_min == pytest.approx(900.0)  # Z16 = 1.5*B
    assert passo_max == pytest.approx(237.6)  # Z18 = min(1000/3, 0.8*z)


@pytest.mark.unit
def test_limiti_staffe_fixed_keeps_ntc_1_5b_floor_as_a_minimum_not_a_replacement():
    """NTC2018 §4.1.6.1.1's Ast=1.5*b mm²/m is a mandatory floor, not a pre-Eurocode rule of
    thumb: EC2 9.2.2(5) rho_w,min is an ADDITIONAL floor, so fixed mode must return the max of
    the two, never a value below 1.5*b (regression check: this used to drop to 567.94)."""
    ast_min, passo_max = limiti_staffe(b_mm=B_MM, d_mm=D_MM, z_mm=Z_MM, fck_MPa=FCK_MPA, fyk_MPa=FYK_MPA, legacy_compat=False)
    assert ast_min == pytest.approx(900.0)  # max(1.5*600, 567.94) = 900 (NTC floor governs)
    assert passo_max == pytest.approx(264.0)  # min(330, 1000/3, 0.8*d)


@pytest.mark.unit
def test_limiti_staffe_fixed_ec2_floor_governs_for_high_strength_low_grade_steel():
    """When rho_w,min*b*1000 exceeds 1.5*b (very high fck / low fyk), the EC2 floor governs."""
    ast_min, _ = limiti_staffe(b_mm=B_MM, d_mm=D_MM, z_mm=Z_MM, fck_MPa=90.0, fyk_MPa=450.0, legacy_compat=False)
    rho_w_min = 0.08 * 90.0**0.5 / 450.0
    expected = max(1.5 * B_MM, rho_w_min * B_MM * 1000.0)
    assert ast_min == pytest.approx(expected, rel=1e-6)
    assert ast_min > 1.5 * B_MM


@pytest.mark.unit
def test_as_max_is_4_percent_of_gross_area_both_modes():
    for legacy in (True, False):
        out = armatura_minima_massima(
            b_mm=600, h_mm=400, d_mm=D_MM, z_mm=Z_MM,
            n_ferri1=5, diametro_ferri1_mm=20, n_ferri2=0, diametro_ferri2_mm=0,
            diametro_staffe1_mm=12, n_bracci_staffe1=2, passo_staffe1_mm=115,
            diametro_staffe2_mm=0, n_bracci_staffe2=0,
            fck_MPa=FCK_MPA, fctm_MPa=FCTM_MPA, fyk_MPa=FYK_MPA, ftk_MPa=FTK_MPA, classe_duttilita="CDB", legacy_compat=legacy,
        )
        assert out.as_max_mm2 == pytest.approx(9600.0)


@pytest.mark.unit
def test_area_ferri_ignores_unused_second_bar_type():
    out = armatura_minima_massima(
        b_mm=600, h_mm=400, d_mm=D_MM, z_mm=Z_MM,
        n_ferri1=5, diametro_ferri1_mm=20, n_ferri2=0, diametro_ferri2_mm=0,
        diametro_staffe1_mm=12, n_bracci_staffe1=2, passo_staffe1_mm=115,
        diametro_staffe2_mm=0, n_bracci_staffe2=0,
        fck_MPa=FCK_MPA, fctm_MPa=FCTM_MPA, fyk_MPa=FYK_MPA, ftk_MPa=FTK_MPA, classe_duttilita="CDB", legacy_compat=False,
    )
    assert out.as_o_mm2 == pytest.approx(1570.796, rel=1e-5)


@pytest.mark.unit
def test_stirrups_area_per_m_sums_both_types_over_shared_spacing():
    out = armatura_minima_massima(
        b_mm=600, h_mm=400, d_mm=D_MM, z_mm=Z_MM,
        n_ferri1=5, diametro_ferri1_mm=20, n_ferri2=0, diametro_ferri2_mm=0,
        diametro_staffe1_mm=12, n_bracci_staffe1=2, passo_staffe1_mm=115,
        diametro_staffe2_mm=8, n_bracci_staffe2=2, fck_MPa=FCK_MPA, fctm_MPa=FCTM_MPA, fyk_MPa=FYK_MPA,
        ftk_MPa=FTK_MPA, classe_duttilita="CDB", legacy_compat=False,
    )
    # AM33*1000/H16 with combined stirrup area (type1 + type2), shared passo (H19=H16 in the sheet)
    assert out.asw_per_m_mm2 == pytest.approx(1966.91 + 2 * (3.14159265 / 4 * 8**2) * 1000 / 115, rel=1e-4)


@pytest.mark.unit
def test_duttilita_longitudinale_sismica_matches_ntc2018_7_4_6_2_1():
    """MEDIUM finding: §7.4.6.2.1 rho limits/compression-steel ratio are never checked by the
    sheet; golden case (only ferri1, no ferri2) fails both the rho_max cap and the As' minimum."""
    rho, rho_min, rho_max, as_comp_min_mm2 = duttilita_longitudinale_sismica(
        b_mm=600.0, d_mm=330.0, as_tesa_mm2=1570.7963267948967, as_comp_mm2=0.0, fyk_MPa=500.0, classe="CDB"
    )
    assert rho == pytest.approx(1570.7963267948967 / (600.0 * 330.0), rel=1e-6)
    assert rho_min == pytest.approx(1.4 / 500.0, rel=1e-6)
    assert rho_max == pytest.approx(3.5 / 500.0, rel=1e-6)  # rho_comp=0
    assert as_comp_min_mm2 == pytest.approx(0.25 * 1570.7963267948967, rel=1e-6)  # CDB: 25%
    assert rho > rho_max  # golden case over-reinforced for the seismic ductility cap


@pytest.mark.unit
def test_duttilita_longitudinale_sismica_cda_requires_50_percent_compression_steel():
    _, _, _, as_comp_min_mm2 = duttilita_longitudinale_sismica(
        b_mm=600.0, d_mm=330.0, as_tesa_mm2=1000.0, as_comp_mm2=0.0, fyk_MPa=450.0, classe="CDA"
    )
    assert as_comp_min_mm2 == pytest.approx(500.0)  # CDA: 50%


@pytest.mark.unit
def test_armatura_minima_massima_exposes_seismic_ductility_fields():
    out = armatura_minima_massima(
        b_mm=600, h_mm=400, d_mm=D_MM, z_mm=Z_MM,
        n_ferri1=5, diametro_ferri1_mm=20, n_ferri2=0, diametro_ferri2_mm=0,
        diametro_staffe1_mm=12, n_bracci_staffe1=2, passo_staffe1_mm=115,
        diametro_staffe2_mm=0, n_bracci_staffe2=0,
        fck_MPa=FCK_MPA, fctm_MPa=FCTM_MPA, fyk_MPa=FYK_MPA, ftk_MPa=FTK_MPA, classe_duttilita="CDB", legacy_compat=False,
    )
    assert out.as_comp_mm2 == pytest.approx(0.0)
    assert out.rho_tesa == pytest.approx(1570.7963267948967 / (600.0 * 330.0), rel=1e-5)
    assert out.rho_min_sismico == pytest.approx(1.4 / 500.0, rel=1e-6)
    assert out.as_comp_min_sismico_mm2 == pytest.approx(0.25 * 1570.7963267948967, rel=1e-6)

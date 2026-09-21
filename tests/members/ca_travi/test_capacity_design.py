import pytest

from strutture.members.ca_travi.capacity_design import (
    dettagli_costruttivi,
    lunghezza_ancoraggio_mm,
    lunghezza_critica_mm,
    passo_max_zona_critica_mm,
    taglio_capacity_design_kN,
)


@pytest.mark.unit
def test_lunghezza_critica_cda_is_1_5_h():
    assert lunghezza_critica_mm(400, "CDA") == pytest.approx(600)
    assert lunghezza_critica_mm(400, "CDB") == pytest.approx(400)


@pytest.mark.unit
def test_passo_max_legacy_degenerates_to_zero_when_second_bar_type_unused():
    """Divergence: sheet's K60 forces p,max to 0 via 8*MIN(ø1,ø2)=0 when ø2 (unused type) is 0,
    not via MIN(staffe1,staffe2) as the spec write-up suggested (K60 only references H15)."""
    p_max = passo_max_zona_critica_mm(
        h_mm=400, d_mm=330, classe="CDB",
        diametro_staffe1_mm=12, diametro_staffe2_mm=0, n_bracci_staffe2=0,
        diametro_ferri1_mm=20, n_ferri1=5, diametro_ferri2_mm=0, n_ferri2=0,
        legacy_compat=True,
    )
    assert p_max == pytest.approx(0.0)


@pytest.mark.unit
def test_passo_max_fixed_ignores_unused_bar_type():
    p_max = passo_max_zona_critica_mm(
        h_mm=400, d_mm=330, classe="CDB",
        diametro_staffe1_mm=12, diametro_staffe2_mm=0, n_bracci_staffe2=0,
        diametro_ferri1_mm=20, n_ferri1=5, diametro_ferri2_mm=0, n_ferri2=0,
        legacy_compat=False,
    )
    assert p_max == pytest.approx(min(330 / 4, 24 * 12, 225, 8 * 20))
    assert p_max == pytest.approx(82.5)


@pytest.mark.unit
def test_passo_max_fixed_uses_both_bar_types_when_present():
    p_max = passo_max_zona_critica_mm(
        h_mm=400, d_mm=330, classe="CDA",
        diametro_staffe1_mm=8, diametro_staffe2_mm=8, n_bracci_staffe2=2,
        diametro_ferri1_mm=16, n_ferri1=3, diametro_ferri2_mm=16, n_ferri2=2,
        legacy_compat=False,
    )
    assert p_max == pytest.approx(min(330 / 4, 24 * 8, 175, 6 * 16))


@pytest.mark.unit
def test_passo_max_fixed_uses_effective_depth_not_gross_height():
    """CRITICAL finding: NTC2018 §7.4.6.2.1 requires d/4 (altezza utile), not h/4 (altezza
    lorda); golden case h=400/d=330 gives 100mm (h/4, non-conservative) vs 82.5mm (d/4)."""
    p_max_d4_governs = passo_max_zona_critica_mm(
        h_mm=400, d_mm=330, classe="CDB",
        diametro_staffe1_mm=12, diametro_staffe2_mm=0, n_bracci_staffe2=0,
        diametro_ferri1_mm=20, n_ferri1=5, diametro_ferri2_mm=0, n_ferri2=0,
        legacy_compat=False,
    )
    assert p_max_d4_governs == pytest.approx(330 / 4)
    assert p_max_d4_governs < 100.0  # strictly tighter than the old (wrong) h/4=100mm


@pytest.mark.unit
def test_lunghezza_ancoraggio_uses_max_stirrup_diameter():
    assert lunghezza_ancoraggio_mm(12, 0) == pytest.approx(120)
    assert lunghezza_ancoraggio_mm(12, 16) == pytest.approx(160)


@pytest.mark.unit
def test_taglio_capacity_design_legacy_reproduces_sheet_k81_moment_labelled_as_kn():
    """legacy_compat=True keeps K81 exactly (dimensionally a moment, Lt unused) — sheet bug."""
    assert taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8, legacy_compat=True) == pytest.approx(207.01, rel=1e-5)


@pytest.mark.unit
def test_taglio_capacity_design_legacy_ignores_lt():
    a = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8, legacy_compat=True)
    b = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=4, legacy_compat=True)
    assert a == pytest.approx(b)


@pytest.mark.unit
def test_taglio_capacity_design_caps_at_column_capacity_ratio():
    # MRc < MRb: MIN(1, MRc/MRb) < 1
    result = taglio_capacity_design_kN(mrb_kNm=207.01, mrc_kNm=100.0, classe="CDA", lt_m=8, legacy_compat=True)
    assert result == pytest.approx(1.2 * 207.01 * (100.0 / 207.01), rel=1e-6)


@pytest.mark.unit
def test_taglio_capacity_design_fixed_uses_lt_ntc2018_7_4_4_1_1():
    """HIGH finding: NTC2018 §7.4.4.1.1 VEd = (Mi,d+Mj,d)/Lt; fixed mode must use `lt_m` and
    return a force, not a bare moment."""
    result = taglio_capacity_design_kN(mrb_kNm=207.01, mrc_kNm=350, classe="CDB", lt_m=8, legacy_compat=False)
    fattore = min(1.0, 350 / 207.01)
    expected = 2.0 * 1.0 * 207.01 * fattore / 8
    assert result == pytest.approx(expected, rel=1e-6)
    assert result == pytest.approx(51.7525, rel=1e-4)


@pytest.mark.unit
def test_taglio_capacity_design_fixed_scales_inversely_with_lt():
    short_span = taglio_capacity_design_kN(mrb_kNm=207.01, mrc_kNm=350, classe="CDB", lt_m=4, legacy_compat=False)
    long_span = taglio_capacity_design_kN(mrb_kNm=207.01, mrc_kNm=350, classe="CDB", lt_m=8, legacy_compat=False)
    assert short_span == pytest.approx(2.0 * long_span, rel=1e-6)


@pytest.mark.unit
def test_dettagli_costruttivi_composes_all_four_outputs():
    out = dettagli_costruttivi(
        h_mm=400, d_mm=330, classe="CDB",
        diametro_staffe1_mm=12, diametro_staffe2_mm=0, n_bracci_staffe2=0,
        diametro_ferri1_mm=20, n_ferri1=5, diametro_ferri2_mm=0, n_ferri2=0,
        mrb_kNm=207.01, mrc_kNm=350, lt_m=8, legacy_compat=True,
    )
    assert out.lunghezza_critica_mm == pytest.approx(400)
    assert out.passo_max_zona_critica_mm == pytest.approx(0.0)
    assert out.lunghezza_ancoraggio_mm == pytest.approx(120)
    assert out.ved_max_kN == pytest.approx(207.01, rel=1e-4)


# --- NTC2018 §7.4.4.1.1: the gravity-load shear is ADDED to the shear from the end moments ----------

def test_gravity_shear_is_added_to_the_capacity_design_shear():
    senza = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8)
    con = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8, v_gravita_kN=40.0)
    assert senza == pytest.approx(2 * 207.01 / 8)
    assert con == pytest.approx(senza + 40.0)


def test_excel_mode_ignores_the_gravity_shear_like_the_sheet():
    a = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8, legacy_compat=True)
    b = taglio_capacity_design_kN(207.01, 350, "CDB", lt_m=8, v_gravita_kN=40.0, legacy_compat=True)
    assert a == b

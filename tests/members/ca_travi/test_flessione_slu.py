import pytest

from strutture.members.ca_travi.flessione_slu import (
    momento_resistente_kNm,
    profondita_asse_neutro_mm,
    verifica_flessione_slu,
)

AS_O_MM2, FYD_MPA, FCD_MPA, B_MM, D_MM = 1570.7963267948967, 434.7826086956522, 21.165, 600.0, 330.0
ES_MPA = 210000.0


@pytest.mark.unit
def test_profondita_asse_neutro_legacy_matches_golden_sheet_z32():
    """legacy_compat=True reproduces the sheet's 0.81 factor (Z32=66.395)."""
    assert profondita_asse_neutro_mm(AS_O_MM2, FYD_MPA, B_MM, FCD_MPA, legacy_compat=True) == pytest.approx(66.3953, rel=1e-5)


@pytest.mark.unit
def test_profondita_asse_neutro_fixed_uses_0_8_ntc2018_4_1_2_3_4_2():
    """MEDIUM finding: NTC2018 §4.1.2.3.4.2 fixes lambda=0.8 (fck<=50MPa), not the sheet's 0.81;
    fixed y is ~1.25% above the legacy value (the true neutral axis depth)."""
    legacy = profondita_asse_neutro_mm(AS_O_MM2, FYD_MPA, B_MM, FCD_MPA, legacy_compat=True)
    fixed = profondita_asse_neutro_mm(AS_O_MM2, FYD_MPA, B_MM, FCD_MPA, legacy_compat=False)
    assert fixed != pytest.approx(legacy)
    assert fixed == pytest.approx(legacy * 0.81 / 0.8, rel=1e-6)


@pytest.mark.unit
def test_momento_resistente_matches_golden_both_modes():
    """MRd is unaffected by the stress-block-factor divergence: the same factor is used to
    compute y and to weight it back, so it cancels out algebraically in both modes."""
    for legacy_compat in (True, False):
        y_mm = profondita_asse_neutro_mm(AS_O_MM2, FYD_MPA, B_MM, FCD_MPA, legacy_compat=legacy_compat)
        assert momento_resistente_kNm(AS_O_MM2, FYD_MPA, D_MM, y_mm, legacy_compat=legacy_compat) == pytest.approx(
            207.010, rel=1e-5
        )


@pytest.mark.unit
def test_verifica_flessione_slu_computes_tasso_sfruttamento():
    out = verifica_flessione_slu(
        as_o_mm2=AS_O_MM2, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, b_mm=B_MM, d_mm=D_MM, med_slu_kNm=318, es_MPa=ES_MPA,
        legacy_compat=True,
    )
    assert out.mrd_kNm == pytest.approx(207.010, rel=1e-5)
    assert out.tasso_sfruttamento == pytest.approx(318 / 207.010, rel=1e-4)
    assert out.d_mm == pytest.approx(D_MM)


@pytest.mark.unit
def test_verifica_flessione_slu_reports_steel_yielded_for_golden_case():
    """MEDIUM finding: add a ductility/compatibility check (eps_s vs eps_yd) rather than trusting
    MRd unconditionally; golden case is heavily under-reinforced so steel yields."""
    out = verifica_flessione_slu(
        as_o_mm2=AS_O_MM2, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, b_mm=B_MM, d_mm=D_MM, med_slu_kNm=318, es_MPa=ES_MPA,
        legacy_compat=False,
    )
    assert out.acciaio_snervato is True
    assert out.eps_s_permille > FYD_MPA / ES_MPA * 1000.0


@pytest.mark.unit
def test_verifica_flessione_slu_detects_over_reinforced_non_yielding_steel():
    """A heavily over-reinforced section (large As, small b/d) should NOT be reported as
    yielded."""
    out = verifica_flessione_slu(
        as_o_mm2=50_000.0, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, b_mm=B_MM, d_mm=D_MM, med_slu_kNm=1.0, es_MPa=ES_MPA,
        legacy_compat=False,
    )
    assert out.acciaio_snervato is False

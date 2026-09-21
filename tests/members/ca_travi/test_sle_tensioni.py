import pytest

from strutture.members.ca_travi.sle_tensioni import (
    braccio_leva_elastico_mm,
    limite_sigma_acciaio_MPa,
    sigma_acciaio_MPa,
    sigma_calcestruzzo_MPa,
    verifica_sle_tensioni,
)

B_MM, D_MM, AS_O_MM2 = 600.0, 330.0, 1570.8
MED_RARA_KNM, MED_QP_KNM = 239.0, 200.0
FCK_MPA_LEGACY = 37.35  # C35/45, legacy fck=0.83*Rck (see docs/divergences/materials.md)


@pytest.mark.unit
def test_braccio_leva_elastico_matches_golden():
    assert braccio_leva_elastico_mm(D_MM, 126.44148274754764) == pytest.approx(330.0 - 126.44148274754764 / 3.0, rel=1e-6)


@pytest.mark.unit
def test_sigma_calcestruzzo_matches_golden_z39():
    braccio_mm = braccio_leva_elastico_mm(D_MM, 126.44148274754764)
    assert sigma_calcestruzzo_MPa(MED_RARA_KNM, B_MM, 126.44148274754764, braccio_mm) == pytest.approx(21.8885, rel=1e-4)


@pytest.mark.unit
def test_sigma_acciaio_matches_golden_z41():
    braccio_mm = braccio_leva_elastico_mm(D_MM, 126.44148274754764)
    assert sigma_acciaio_MPa(MED_RARA_KNM, AS_O_MM2, braccio_mm) == pytest.approx(528.576, rel=1e-4)


@pytest.mark.unit
def test_limite_sigma_acciaio_legacy_is_hardcoded_360():
    """Z42 bug: the sheet hardcodes 360 MPa regardless of the selected steel grade."""
    assert limite_sigma_acciaio_MPa(215.0, legacy_compat=True) == pytest.approx(360.0)
    assert limite_sigma_acciaio_MPa(500.0, legacy_compat=True) == pytest.approx(360.0)


@pytest.mark.unit
def test_limite_sigma_acciaio_fixed_uses_080_fyk():
    """Fixed mode: 0.80*fyk, correct for any steel grade (docs/divergences/ca-travi.md)."""
    assert limite_sigma_acciaio_MPa(215.0, legacy_compat=False) == pytest.approx(0.80 * 215.0)
    assert limite_sigma_acciaio_MPa(450.0, legacy_compat=False) == pytest.approx(360.0)  # B450C: fixed == legacy


@pytest.mark.unit
def test_verifica_sle_tensioni_matches_golden_case():
    out = verifica_sle_tensioni(
        b_mm=B_MM, d_mm=D_MM, as_o_mm2=AS_O_MM2, med_rara_kNm=MED_RARA_KNM, med_qp_kNm=MED_QP_KNM,
        fck_MPa=FCK_MPA_LEGACY, fyk_MPa=500.0, combinazione="Frequente", legacy_compat=True,
    )
    assert out.x_mm == pytest.approx(126.44, rel=1e-4)
    assert out.sigma_c_rara_MPa == pytest.approx(21.8885, rel=1e-4)
    assert out.sigma_s_rara_MPa == pytest.approx(528.576, rel=1e-4)
    assert out.sigma_c_qp_MPa == pytest.approx(18.3168, rel=1e-4)
    assert out.limite_sigma_c_rara_MPa == pytest.approx(0.60 * FCK_MPA_LEGACY)
    assert out.limite_sigma_c_qp_MPa == pytest.approx(0.45 * FCK_MPA_LEGACY)
    assert out.limite_sigma_s_MPa == pytest.approx(360.0)
    # combinazione="Frequente" -> sigma_s_combinazione uses the rara value.
    assert out.sigma_s_combinazione_MPa == pytest.approx(out.sigma_s_rara_MPa)


@pytest.mark.unit
def test_verifica_sle_tensioni_quasi_permanente_uses_sigma_s_qp():
    out = verifica_sle_tensioni(
        b_mm=B_MM, d_mm=D_MM, as_o_mm2=AS_O_MM2, med_rara_kNm=MED_RARA_KNM, med_qp_kNm=MED_QP_KNM,
        fck_MPa=FCK_MPA_LEGACY, fyk_MPa=500.0, combinazione="Quasi permanente", legacy_compat=False,
    )
    assert out.sigma_s_combinazione_MPa == pytest.approx(out.sigma_s_qp_MPa)
    assert out.sigma_s_combinazione_MPa != pytest.approx(out.sigma_s_rara_MPa)
    assert out.limite_sigma_s_MPa == pytest.approx(0.80 * 500.0)

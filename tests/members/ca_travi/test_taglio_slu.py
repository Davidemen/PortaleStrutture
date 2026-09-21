import pytest

from strutture.members.ca_travi.taglio_slu import cotangente_puntoni, verifica_taglio_slu
from strutture.shared.report import CalcError

B_MM, Z_MM, FYD_MPA, FCD_MPA = 600.0, 297.0, 434.7826086956522, 21.165


@pytest.mark.unit
def test_cotangente_puntoni_clamps_at_upper_bound():
    # golden case: sin^2(theta) small -> raw cotg > 2.5, clamped
    asw_per_mm = 1966.9101831170879 / 1000.0
    assert cotangente_puntoni(asw_per_mm, FYD_MPA, B_MM, FCD_MPA) == pytest.approx(2.5)


@pytest.mark.unit
def test_cotangente_puntoni_clamps_at_lower_bound():
    # heavy stirrups (4 legs, ø16 @80mm) -> sin^2(theta) large -> raw cotg < 1, clamped
    asw_per_m = 4 * (3.14159265358979 / 4 * 16**2) * 1000 / 80
    assert cotangente_puntoni(asw_per_m / 1000.0, FYD_MPA, B_MM, FCD_MPA) == pytest.approx(1.0)


@pytest.mark.unit
def test_cotangente_puntoni_rejects_over_reinforced_shear():
    # matches the sheet's #NUM! for this input combination (LibreOffice-verified)
    asw_per_m = 4 * (3.14159265358979 / 4 * 20**2) * 1000 / 50
    with pytest.raises(CalcError):
        cotangente_puntoni(asw_per_m / 1000.0, FYD_MPA, B_MM, FCD_MPA)


@pytest.mark.unit
def test_verifica_taglio_slu_matches_golden():
    out = verifica_taglio_slu(
        b_mm=B_MM, z_mm=Z_MM, asw_per_m_mm2=1966.9101831170879, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, alpha_staffe_deg=90
    )
    assert out.cotg_theta == pytest.approx(2.5)
    assert out.vrdc_kN == pytest.approx(650.276, rel=1e-5)
    assert out.vrds_kN == pytest.approx(634.970, rel=1e-5)
    assert out.vrd_kN == pytest.approx(634.970, rel=1e-5)


@pytest.mark.unit
def test_verifica_taglio_slu_inclined_stirrups_differ_from_vertical():
    vertical = verifica_taglio_slu(
        b_mm=B_MM, z_mm=Z_MM, asw_per_m_mm2=1966.9101831170879, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, alpha_staffe_deg=90
    )
    inclined = verifica_taglio_slu(
        b_mm=B_MM, z_mm=Z_MM, asw_per_m_mm2=1966.9101831170879, fyd_MPa=FYD_MPA, fcd_MPa=FCD_MPA, alpha_staffe_deg=60
    )
    assert inclined.vrd_kN != pytest.approx(vertical.vrd_kN)

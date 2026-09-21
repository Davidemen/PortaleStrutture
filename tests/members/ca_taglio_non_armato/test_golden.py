import pytest

from strutture.members.ca_taglio_non_armato.compose import run
from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput


@pytest.mark.golden
def test_golden_case():
    """Spec §8: Rck=35MPa, h=500mm, c=50mm, bw=1000mm, Asl=1005mm2, NEd=0kN (sheet Foglio1)."""
    report = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, legacy_compat=True))
    assert report.ok
    data = report.data

    assert data.materiali.fck_MPa == pytest.approx(29.05, rel=1e-6)
    assert data.materiali.fcd_MPa == pytest.approx(16.4617, rel=1e-4)
    assert data.geometria.d_mm == pytest.approx(450, rel=1e-6)
    assert data.taglio.sigma_cp_MPa == pytest.approx(0, abs=1e-9)
    assert data.taglio.k == pytest.approx(1.66667, rel=1e-4)
    assert data.taglio.vmin_MPa == pytest.approx(0.405896, rel=1e-5)
    assert data.taglio.rho_l == pytest.approx(0.00223333, rel=1e-5)
    assert data.taglio.vrd1_kN == pytest.approx(167.858, rel=1e-5)
    assert data.taglio.vrd2_kN == pytest.approx(182.653, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(182.653, rel=1e-5)


@pytest.mark.golden
def test_golden_case_v2():
    """docs/specs/small-units.md, ca-taglio-non-armato-v2, sheet `1m`: Rck=40, fck=32 (direct),
    gamma_c=1.5, h=250mm, c=68mm, bw=1000mm, N=5, diametro=12mm, NEd=0."""
    report = run(
        TaglioNonArmatoInput(
            rck_MPa=40, fck_MPa=32, h_mm=250, c_mm=68, bw_mm=1000,
            n_barre=5, diametro_barre_mm=12, ned_kN=0, legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.materiali.fck_MPa == pytest.approx(32, rel=1e-9)
    assert data.materiali.fcd_MPa == pytest.approx(18.1333, rel=1e-4)
    assert data.geometria.d_mm == pytest.approx(182, rel=1e-6)
    assert data.geometria.asl_mm2 == pytest.approx(565.487, rel=1e-5)
    assert data.taglio.sigma_cp_MPa == pytest.approx(0, abs=1e-9)
    assert data.taglio.k == pytest.approx(2, rel=1e-6)
    assert data.taglio.vmin_MPa == pytest.approx(0.56, rel=1e-5)
    assert data.taglio.rho_l == pytest.approx(0.00310707, rel=1e-5)
    assert data.taglio.vrd1_kN == pytest.approx(93.9254, rel=1e-5)
    assert data.taglio.vrd2_kN == pytest.approx(101.92, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(101.92, rel=1e-5)

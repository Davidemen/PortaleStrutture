"""docs/specs/ca-pilastri-ec2.md §8 golden cases (norma="EC2", legacy_compat=True),
pytest.approx(rel=1e-6). Same inputs as the base/NTC2018 golden cases.

Note on `i` (radius of gyration, rectangular case): the delta spec's prose calls this "unchanged,
net/core-section" (~86.6mm) but its own golden case lists `lambda=30.3109`, which is only
consistent with the GROSS `i=115.47` (matches `l0/i = 3500/115.47`); direct inspection of the
workbook formula (`build/cellmaps/ca-pilastri-ec2/ret-uni-en-1992-1-1-2005.txt`, "Raggio d'inerzia"
row) confirms it is byte-identical to the NTC2018 sheet's gross-section formula. This test follows
the verified formula + the spec's own numbers, not its (inconsistent) prose."""
import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare


@pytest.mark.golden
def test_golden_pilastro_rettangolare_ec2():
    inputs = PilastroRettangolareInput(
        norma="EC2", l1_mm=400, l2_mm=400, h_mm=3500, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=8,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, n_ferri_l1=3, legacy_compat=True,
    )
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    data = report.data

    assert data.regole.nu1 == pytest.approx(0.54024, rel=1e-4)
    assert data.taglio.vrdc_kN == pytest.approx(387.883, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(322.696, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(322.696, rel=1e-5)
    assert data.regole.omega_meccanico == pytest.approx(0.278797, rel=1e-5)
    assert data.snellezza.lambda_lim == pytest.approx(16.7759, rel=1e-5)
    assert data.snellezza.l0_mm == pytest.approx(3500, rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(30.3109, rel=1e-5)
    assert data.armatura_minima.as_min_mm2 == pytest.approx(320.0, rel=1e-5)  # MAX(320, 306.667), EC2's own coefficient 0.002

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["taglio"] is True
    assert by_name["gerarchia_resistenze"] is True
    assert by_name["diametro_minimo_longitudinale"] is True  # 16mm > 8mm (EC2 threshold, not 12mm)
    assert by_name["area_minima_longitudinale"] is True
    assert by_name["area_massima_longitudinale"] is True  # EC2-only standalone check, 1608.5 <= 6400
    # Headline behavioural divergence: EC2's own slenderness formula genuinely fails this geometry
    # (30.31 > 16.78), unlike the NTC2018 sheet's "OK" for the identical inputs.
    assert by_name["snellezza"] is False


@pytest.mark.golden
def test_golden_pilastro_circolare_ec2():
    inputs = PilastroCircolareInput(
        norma="EC2", d_mm=400, h_mm=5000, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=25,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, legacy_compat=True,
    )
    report = run_pilastro_circolare(inputs)
    assert report.ok
    data = report.data

    assert data.regole.nu1 == pytest.approx(0.54024, rel=1e-4)
    assert data.taglio.vrdc_kN == pytest.approx(240.586, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(222.666, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(222.666, rel=1e-5)
    assert data.regole.omega_meccanico == pytest.approx(1.1093, rel=1e-4)
    assert data.snellezza.lambda_lim == pytest.approx(21.3716, rel=1e-5)
    assert data.snellezza.l0_mm == pytest.approx(5000, rel=1e-6)
    assert data.snellezza.i_mm == pytest.approx(100, rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(50, rel=1e-6)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["taglio"] is True
    assert by_name["gerarchia_resistenze"] is True
    assert by_name["snellezza"] is False  # 50 > 21.37, FAILS (same headline pattern as rect)

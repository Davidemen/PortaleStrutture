"""Spec §8 golden cases (legacy_compat=True), pytest.approx(rel=1e-6). `norma="NTC2008"` is
explicit here (architecture-batch2.md §3: "Only mechanical edit to batch-1 tests") because these
assert the original 2008 sheet's own (buggy) numbers; the default `norma="NTC2018"` would give a
different λlim/i (see test_golden_ntc2018.py / test_golden_ec2.py for the new sheets)."""
import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare


@pytest.mark.golden
def test_golden_pilastro_rettangolare():
    inputs = PilastroRettangolareInput(
        l1_mm=400, l2_mm=400, h_mm=3500, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=8,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, n_ferri_l1=3, legacy_compat=True, norma="NTC2008",
    )
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    data = report.data

    assert data.materiali.fyd_MPa == pytest.approx(391.304, rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(14.11, rel=1e-6)
    assert data.geometria.ac_mm2 == pytest.approx(160000, rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(1608.5, rel=1e-5)
    assert data.geometria.rs == pytest.approx(0.0100531, rel=1e-5)
    assert data.geometria.e_min_mm == pytest.approx(20, rel=1e-6)
    assert data.geometria.med_ecc_kNm == pytest.approx(24, rel=1e-6)
    assert data.geometria.med_calc_kNm == pytest.approx(80, rel=1e-6)
    assert data.taglio.sigma_cp_MPa == pytest.approx(7.5, rel=1e-6)
    assert data.taglio.ac == pytest.approx(1.17116, rel=1e-5)
    assert data.taglio.cot_theta == pytest.approx(2.5, rel=1e-6)
    assert data.taglio.vrdc_kN == pytest.approx(358.991, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(322.696, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(322.696, rel=1e-5)
    assert data.flessione.tasso_sfruttamento_pct == pytest.approx(50, rel=1e-6)
    assert data.compressione.nrcd_kN == pytest.approx(2257.6, rel=1e-6)
    assert data.compressione.tasso_sfruttamento_pct == pytest.approx(53.15, rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(1084.36, rel=1e-4)
    assert data.snellezza.i_mm == pytest.approx(86.6025, rel=1e-5)
    assert data.snellezza.l0_mm == pytest.approx(3000, rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(34.641, rel=1e-5)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Resistenza a taglio"] is True
    assert by_name["Gerarchia delle resistenze a taglio"] is True
    assert by_name["Percentuale di armatura longitudinale"] is True
    assert by_name["Resistenza a pressoflessione"] is True
    assert by_name["Resistenza a compressione"] is True
    assert by_name["Verifica di snellezza"] is True
    for name in (
        "Diametro minimo delle barre longitudinali", "Interasse massimo delle barre longitudinali", "Area minima di armatura longitudinale",
        "Diametro minimo delle staffe", "Interasse massimo delle staffe",
    ):
        assert by_name[name] is True, name


@pytest.mark.golden
def test_golden_pilastro_circolare():
    inputs = PilastroCircolareInput(
        d_mm=400, h_mm=5000, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=25,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, legacy_compat=True, norma="NTC2008",
    )
    report = run_pilastro_circolare(inputs)
    assert report.ok
    data = report.data

    assert data.materiali.fyd_MPa == pytest.approx(391.304, rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(14.11, rel=1e-6)
    assert data.geometria.ac_mm2 == pytest.approx(125664, rel=1e-5)
    assert data.geometria.as_mm2 == pytest.approx(5026.55, rel=1e-5)
    assert data.geometria.rs == pytest.approx(0.04, rel=1e-6)
    assert data.geometria.lato_equivalente_mm == pytest.approx(354.491, rel=1e-5)
    assert data.taglio.vrdc_kN == pytest.approx(222.666, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(222.666, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(222.666, rel=1e-5)
    assert data.flessione.tasso_sfruttamento_pct == pytest.approx(50, rel=1e-6)
    assert data.compressione.nrcd_kN == pytest.approx(1773.11, rel=1e-5)
    assert data.compressione.tasso_sfruttamento_pct == pytest.approx(67.68, rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(960.988, rel=1e-5)
    assert data.snellezza.i_mm == pytest.approx(75, rel=1e-6)
    assert data.snellezza.l0_mm == pytest.approx(3000, rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(40, rel=1e-6)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Resistenza a taglio"] is True
    assert by_name["Gerarchia delle resistenze a taglio"] is True
    assert by_name["Percentuale di armatura longitudinale"] is False  # rs=0.04 is not strictly < 0.04
    assert by_name["Resistenza a pressoflessione"] is True
    assert by_name["Resistenza a compressione"] is True
    assert by_name["Verifica di snellezza"] is True
    for name in (
        "Diametro minimo delle barre longitudinali", "Interasse massimo delle barre longitudinali", "Area minima di armatura longitudinale",
        "Diametro minimo delle staffe", "Interasse massimo delle staffe",
    ):
        assert by_name[name] is True, name

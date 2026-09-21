"""docs/specs/ca-pilastri-ntc2018.md §8 golden cases (norma="NTC2018", legacy_compat=True),
pytest.approx(rel=1e-6). Same inputs as the NTC2008 golden case; the NTC2018 sheet already fixes
the λlim ×1000 bug and the l0/i formulas, so the numbers genuinely differ from test_golden.py —
notably the circular case's slenderness verdict flips OK -> NO."""
import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare


@pytest.mark.golden
def test_golden_pilastro_rettangolare_ntc2018():
    inputs = PilastroRettangolareInput(
        norma="NTC2018", l1_mm=400, l2_mm=400, h_mm=3500, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=8,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, n_ferri_l1=3, legacy_compat=True,
    )
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    data = report.data

    assert data.taglio.vrdc_kN == pytest.approx(358.991, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(322.696, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(322.696, rel=1e-5)
    assert data.flessione.tasso_sfruttamento_pct == pytest.approx(50, rel=1e-6)
    assert data.compressione.tasso_sfruttamento_pct == pytest.approx(53.15, rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(34.2904, rel=1e-5)  # FIXED: ×1000 bug gone (was 1084.36)
    assert data.snellezza.l0_mm == pytest.approx(3500, rel=1e-6)  # FIXED: l0=H*beta (was hardcoded 3000)
    assert data.snellezza.i_mm == pytest.approx(115.47, rel=1e-5)  # CHANGED: gross section (was 86.6025 net)
    assert data.snellezza.lambda_ == pytest.approx(30.3109, rel=1e-5)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["taglio"] is True
    assert by_name["gerarchia_resistenze"] is True
    assert by_name["percentuale_armatura"] is True  # simplified check: only the 4% ceiling now
    assert by_name["snellezza"] is True
    for name in (
        "diametro_minimo_longitudinale", "interasse_massimo_longitudinale", "area_minima_longitudinale",
        "diametro_minimo_staffe", "interasse_massimo_staffe",
    ):
        assert by_name[name] is True, name


@pytest.mark.golden
def test_golden_pilastro_circolare_ntc2018():
    inputs = PilastroCircolareInput(
        norma="NTC2018", d_mm=400, h_mm=5000, acciaio="B450C", cls="C25/30",
        ned_kN=1200, ved_kN=150, med_kNm=80, c_mm=50, n_ferri=25,
        diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
        mrd_kNm=160, legacy_compat=True,
    )
    report = run_pilastro_circolare(inputs)
    assert report.ok
    data = report.data

    assert data.taglio.vrdc_kN == pytest.approx(222.666, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(222.666, rel=1e-5)
    assert data.compressione.tasso_sfruttamento_pct == pytest.approx(67.68, rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(30.3891, rel=1e-5)  # FIXED (was 960.988)
    assert data.snellezza.l0_mm == pytest.approx(5000, rel=1e-6)  # FIXED (was hardcoded 3000)
    assert data.snellezza.i_mm == pytest.approx(100, rel=1e-6)  # CHANGED: gross D/4 (was 75 net)
    assert data.snellezza.lambda_ == pytest.approx(50, rel=1e-6)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["taglio"] is True
    assert by_name["gerarchia_resistenze"] is True
    assert by_name["percentuale_armatura"] is False  # rs=0.04 not strictly < 0.04
    # Headline regression signal: the fixed λlim/i formulas flip this from OK (NTC2008, λ=40 <
    # λlim=960.988) to NO (NTC2018, λ=50 > λlim=30.39) for the identical geometry.
    assert by_name["snellezza"] is False

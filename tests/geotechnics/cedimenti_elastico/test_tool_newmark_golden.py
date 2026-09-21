import pytest

from strutture.geotechnics.cedimenti_elastico.models_newmark import NewmarkInput
from strutture.geotechnics.cedimenti_elastico.tool_newmark import run_newmark

CENTRO_STRATI = [
    {"z_top_m": 0.80, "z_bot_m": 4.80, "modulo_MPa": 5.5},
    {"z_top_m": 4.80, "z_bot_m": 5.80, "modulo_MPa": 7.0},
    {"z_top_m": 5.80, "z_bot_m": 6.60, "modulo_MPa": 9.0},
    {"z_top_m": 6.60, "z_bot_m": 32.60, "modulo_MPa": 7.0},
    {"z_top_m": 32.60, "z_bot_m": 120.0, "modulo_MPa": 7.0},
]
PUNTO_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 15.0, "modulo_MPa": 100 * 0.0980665},
    {"z_top_m": 15.0, "z_bot_m": 120.0, "modulo_MPa": 180 * 0.0980665},
]


@pytest.mark.golden
def test_centro_golden_case():
    inputs = NewmarkInput(modalita="CENTRO", q=0.5 * 98.0665, d=1.10, b=3.5, l=5.0, strati=CENTRO_STRATI, legacy_compat=True)
    report = run_newmark(inputs)
    assert report.ok, report.errors
    centro = report.data.centro
    assert centro.w_centro_cm == pytest.approx(3.0768, rel=1e-6)
    assert centro.w_qa_cm == pytest.approx(3.0122, abs=2e-4)
    assert centro.w_centro_mm == pytest.approx(centro.w_centro_cm * 10, rel=1e-9)


@pytest.mark.golden
def test_punto_golden_case_500():
    inputs = NewmarkInput(
        modalita="PUNTO", q=0.8 * 98.0665, d=2.20, side_p=40.0, side_q=40.0, e1=20.0, e2=20.0, strati=PUNTO_STRATI, legacy_compat=True
    )
    report = run_newmark(inputs)
    assert report.ok, report.errors
    punto = report.data.punto
    assert punto.w_o_cm == pytest.approx(6.33092, rel=1e-6)
    assert punto.w_o_prime_cm == pytest.approx(1.59762, abs=1e-5)


@pytest.mark.unit
def test_sistema_tecnico_matches_si_for_the_centro_case():
    si = NewmarkInput(modalita="CENTRO", sistema_unita="SI", q=49.03325, d=1.10, b=3.5, l=5.0, strati=CENTRO_STRATI, legacy_compat=True)
    tecnico = NewmarkInput(
        modalita="CENTRO", sistema_unita="tecnico", q=0.5, d=110.0, b=350.0, l=500.0, strati=CENTRO_STRATI, legacy_compat=True
    )
    report_si, report_tecnico = run_newmark(si), run_newmark(tecnico)
    assert report_si.data.centro.w_centro_cm == pytest.approx(report_tecnico.data.centro.w_centro_cm, rel=1e-9)

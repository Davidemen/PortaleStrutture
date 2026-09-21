"""Golden tests: `docs/specs/fond-travi-collegamento.md` §"Golden test case", `legacy_compat=True`."""
import pytest

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.tool import run

_NTC_INPUTS = {
    "norma": "NTC2018", "ag_g": 0.151, "f0": 2.43, "categoria_sottosuolo": "B", "categoria_topografica": "T1",
    "b_mm": 400, "h_mm": 400, "phi_mm": 16, "n_barre": 6, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "phi_staffa_mm": 10, "n_bracci": 2, "cf_mm": 40, "p_mm": 125,
    "legacy_compat": True,
}

_EN_INPUTS = {
    "norma": "EN1998", "ag_g": 0.151, "categoria_sottosuolo": "B", "ms": 5.6,
    "b_mm": 400, "h_mm": 450, "phi_mm": 16, "n_barre": 8, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "n_piani": 3,
    "phi_staffa_mm": 10, "n_bracci": 2, "alpha_staffa_deg": 90, "cf_mm": 40, "p_mm": 200,
    "legacy_compat": True,
}


@pytest.mark.golden
def test_golden_ntc2018() -> None:
    report = run(TraviCollegamentoInput(**_NTC_INPUTS))
    assert report.ok
    data = report.data

    sismica = data.sismica_ntc
    assert sismica.ss == pytest.approx(1.2, rel=1e-5)
    assert sismica.st == pytest.approx(1.0)
    assert sismica.s == pytest.approx(1.2, rel=1e-5)
    assert sismica.amax_g == pytest.approx(0.1812, rel=1e-4)

    assert data.materiali.ac_mm2 == pytest.approx(160000)
    assert data.materiali.as_mm2 == pytest.approx(1206.37, rel=1e-5)
    assert data.materiali.fck_MPa == pytest.approx(24.9, rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(14.11, rel=1e-5)
    assert data.materiali.fyd_MPa == pytest.approx(391.304, rel=1e-5)

    assert data.azione.nsd_kN == pytest.approx(2250)
    assert data.azione.ned_kN == pytest.approx(122.31, rel=1e-5)

    assert data.compressione.ncrd_kN == pytest.approx(2257.6, rel=1e-5)
    assert data.compressione.verifica.passed
    assert data.compressione.tasso_lavoro == pytest.approx(0.054177, rel=1e-4)

    assert data.trazione.ntrd_kN == pytest.approx(472.058, rel=1e-5)
    assert data.trazione.verifica.passed
    assert data.trazione.tasso_lavoro == pytest.approx(0.259099, rel=1e-4)

    snel = data.snellezza_ntc
    assert snel.l0_mm == pytest.approx(5000)
    assert snel.i_mm == pytest.approx(115.47, rel=1e-4)
    assert snel.lambda_ == pytest.approx(43.3013, rel=1e-5)
    assert snel.lambda_lim == pytest.approx(107.407, rel=1e-5)
    assert snel.verifica.passed
    assert snel.tasso_lavoro == pytest.approx(0.403151, rel=1e-4)

    minimi = data.minimi_ntc
    assert minimi.d_mm == pytest.approx(360)
    assert minimi.pmax_mm == pytest.approx(288)
    assert minimi.ast_min_mm2_per_m == pytest.approx(600)
    assert minimi.ast_mm2 == pytest.approx(157.08, rel=1e-4)
    assert minimi.verifica.passed


@pytest.mark.golden
def test_golden_en1998() -> None:
    report = run(TraviCollegamentoInput(**_EN_INPUTS))
    assert report.ok
    data = report.data

    sismica = data.sismica_en
    assert sismica.s == pytest.approx(1.2, rel=1e-5)
    assert sismica.amax_g == pytest.approx(0.1812, rel=1e-4)

    assert data.materiali.ac_mm2 == pytest.approx(180000)
    assert data.materiali.as_mm2 == pytest.approx(1608.5, rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(14.11, rel=1e-5)
    assert data.materiali.fyd_MPa == pytest.approx(391.304, rel=1e-5)

    assert data.azione.nsd_kN == pytest.approx(2250)
    assert data.azione.ned_kN == pytest.approx(122.31, rel=1e-5)

    assert data.compressione.ncrd_kN == pytest.approx(2539.8, rel=1e-5)
    assert data.compressione.verifica.passed
    assert data.compressione.tasso_lavoro == pytest.approx(0.0481573, rel=1e-4)

    assert data.trazione.ntrd_kN == pytest.approx(629.411, rel=1e-5)
    assert data.trazione.verifica.passed
    assert data.trazione.tasso_lavoro == pytest.approx(0.194324, rel=1e-4)

    snel = data.snellezza_en
    assert snel.i_mm == pytest.approx(115.47, rel=1e-4)
    assert snel.omega == pytest.approx(0.247819, rel=1e-4)
    assert snel.lambda_ == pytest.approx(43.3013, rel=1e-5)
    assert snel.lambda_lim == pytest.approx(54.6145, rel=1e-4)
    assert snel.verifica.passed
    assert snel.tasso_lavoro == pytest.approx(0.792853, rel=1e-4)

    minimi = data.minimi_en
    assert minimi.armatura_longitudinale.rho_b_mm2 == pytest.approx(1440)
    assert minimi.armatura_longitudinale.verifica.passed
    assert minimi.geometria.bw_min_mm == pytest.approx(250)
    assert minimi.geometria.verifica_base.passed
    assert minimi.geometria.hw_min_mm == pytest.approx(400)
    assert minimi.geometria.verifica_altezza.passed
    assert minimi.staffe.d_mm == pytest.approx(410)
    assert minimi.staffe.pmax_mm == pytest.approx(307.5, rel=1e-4)
    assert minimi.staffe.rho_min == pytest.approx(0.000887109, rel=1e-4)
    assert minimi.staffe.rho == pytest.approx(0.0019635, rel=1e-4)
    assert minimi.staffe.verifica.passed

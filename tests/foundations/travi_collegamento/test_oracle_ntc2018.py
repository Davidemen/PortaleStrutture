"""Oracle tests for `fond-trave-collegamento` (norma=NTC2018) against
`tests/fixtures/fond_trave_collegamento_ntc2018_oracle.json` (regenerate with
`tests/fixtures/gen_fond_trave_collegamento_ntc2018.py`)."""
import json
from pathlib import Path

import pytest

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.tool import run

FIXTURE = json.loads(Path(__file__).parents[2].joinpath("fixtures", "fond_trave_collegamento_ntc2018_oracle.json").read_text(encoding="utf-8"))

_DEFAULTS = {
    "C4": 0.151, "C5": 2.43, "C6": "B", "C7": "T1", "C11": 400, "C12": 400, "C13": 16, "C14": 6,
    "C17": "C25/30", "C18": "B450C", "C22": 2000, "C23": 2500, "C38": 5000, "C39": 1,
    "C48": 10, "C49": 2, "C50": 40, "C53": 125,
}
_ESITO = {"OK": True, "NO": False}


def _to_input(cells: dict) -> TraviCollegamentoInput:
    merged = {**_DEFAULTS, **cells}
    return TraviCollegamentoInput(
        norma="NTC2018", ag_g=merged["C4"], f0=merged["C5"], categoria_sottosuolo=merged["C6"],
        categoria_topografica=merged["C7"], b_mm=merged["C11"], h_mm=merged["C12"], phi_mm=merged["C13"],
        n_barre=merged["C14"], classe_calcestruzzo=merged["C17"], classe_acciaio=merged["C18"],
        n1_kN=merged["C22"], n2_kN=merged["C23"], l_mm=merged["C38"], beta=merged["C39"],
        phi_staffa_mm=merged["C48"], n_bracci=merged["C49"], cf_mm=merged["C50"], p_mm=merged["C53"],
        legacy_compat=True,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle(case: dict) -> None:
    outputs = case["outputs"]
    report = run(_to_input(case["inputs"]))
    assert report.ok
    data = report.data

    assert data.sismica_ntc.ss == pytest.approx(outputs["C8"], rel=1e-5)
    assert data.sismica_ntc.st == pytest.approx(outputs["C9"], rel=1e-5)
    assert data.sismica_ntc.s == pytest.approx(outputs["C10"], rel=1e-5)
    assert data.materiali.ac_mm2 == pytest.approx(outputs["C15"], rel=1e-5)
    assert data.materiali.as_mm2 == pytest.approx(outputs["C16"], rel=1e-5)
    assert data.materiali.fck_MPa == pytest.approx(outputs["C19"], rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["C20"], rel=1e-5)
    assert data.materiali.fyd_MPa == pytest.approx(outputs["C21"], rel=1e-5)
    assert data.azione.nsd_kN == pytest.approx(outputs["C24"], rel=1e-5)
    assert data.sismica_ntc.amax_g == pytest.approx(outputs["C27"], rel=1e-5)
    assert data.azione.ned_kN == pytest.approx(outputs["C28"], rel=1e-5)
    assert data.compressione.ncrd_kN == pytest.approx(outputs["C29"], rel=1e-5)
    assert data.compressione.verifica.passed == _ESITO[outputs["C30"]]
    assert data.compressione.tasso_lavoro == pytest.approx(outputs["C31"], rel=1e-4)
    assert data.trazione.ntrd_kN == pytest.approx(outputs["C32"], rel=1e-5)
    assert data.trazione.verifica.passed == _ESITO[outputs["C33"]]  # sheet bug: compares vs T.L._c, legacy_compat=True reproduces it
    assert data.trazione.tasso_lavoro == pytest.approx(outputs["C34"], rel=1e-4)
    assert data.snellezza_ntc.l0_mm == pytest.approx(outputs["C40"], rel=1e-5)
    assert data.snellezza_ntc.i_mm == pytest.approx(outputs["C41"], rel=1e-4)
    assert data.snellezza_ntc.lambda_ == pytest.approx(outputs["C42"], rel=1e-4)
    assert data.snellezza_ntc.lambda_lim == pytest.approx(outputs["C43"], rel=1e-4)
    assert data.snellezza_ntc.verifica.passed == _ESITO[outputs["C44"]]
    assert data.snellezza_ntc.tasso_lavoro == pytest.approx(outputs["C45"], rel=1e-4)
    assert data.minimi_ntc.d_mm == pytest.approx(outputs["C51"], rel=1e-5)
    assert data.minimi_ntc.pmax_mm == pytest.approx(outputs["C52"], rel=1e-5)
    assert data.minimi_ntc.ast_min_mm2_per_m == pytest.approx(outputs["C54"], rel=1e-5)
    assert data.minimi_ntc.ast_mm2 == pytest.approx(outputs["C55"], rel=1e-4)
    assert data.minimi_ntc.verifica.passed == _ESITO[outputs["C56"]]

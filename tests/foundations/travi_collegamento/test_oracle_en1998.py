"""Oracle tests for `fond-trave-collegamento` (norma=EN1998) against
`tests/fixtures/fond_trave_collegamento_en1998_oracle.json` (regenerate with
`tests/fixtures/gen_fond_trave_collegamento_en1998.py`)."""
import json
from pathlib import Path

import pytest

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.tool import run
from strutture.shared.report import CalcError

FIXTURE = json.loads(Path(__file__).parents[2].joinpath("fixtures", "fond_trave_collegamento_en1998_oracle.json").read_text(encoding="utf-8"))

_DEFAULTS = {
    "C4": 0.151, "C5": "B", "C6": 5.6, "C9": 400, "C10": 450, "C11": 16, "C12": 8,
    "C15": "C25/30", "C16": "B450C", "C20": 2000, "C21": 2500, "C36": 5000, "C37": 1,
    "C49": 3, "C56": 10, "C57": 2, "C58": 90, "C59": 40, "C62": 200,
}
_ESITO = {"OK": True, "NO": False}


def _to_input(cells: dict) -> TraviCollegamentoInput:
    merged = {**_DEFAULTS, **cells}
    return TraviCollegamentoInput(
        norma="EN1998", ag_g=merged["C4"], categoria_sottosuolo=merged["C5"], ms=merged["C6"],
        b_mm=merged["C9"], h_mm=merged["C10"], phi_mm=merged["C11"], n_barre=merged["C12"],
        classe_calcestruzzo=merged["C15"], classe_acciaio=merged["C16"], n1_kN=merged["C20"], n2_kN=merged["C21"],
        l_mm=merged["C36"], beta=merged["C37"], n_piani=merged["C49"], phi_staffa_mm=merged["C56"],
        n_bracci=merged["C57"], alpha_staffa_deg=merged["C58"], cf_mm=merged["C59"], p_mm=merged["C62"],
        legacy_compat=True,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle(case: dict) -> None:
    outputs = case["outputs"]
    if outputs["C43"] == "#DIV/0!":  # soil A -> alpha=0 -> NEd=0, sheet's λlim formula divides by zero
        with pytest.raises(CalcError):
            run(_to_input(case["inputs"]))
        return

    report = run(_to_input(case["inputs"]))
    assert report.ok
    data = report.data

    assert data.sismica_en.tipo_spettro == outputs["C7"]
    assert data.sismica_en.s == pytest.approx(outputs["C8"], rel=1e-5)
    assert data.materiali.ac_mm2 == pytest.approx(outputs["C13"], rel=1e-5)
    assert data.materiali.as_mm2 == pytest.approx(outputs["C14"], rel=1e-5)
    assert data.materiali.fck_MPa == pytest.approx(outputs["C17"], rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["C18"], rel=1e-5)
    assert data.materiali.fyd_MPa == pytest.approx(outputs["C19"], rel=1e-5)
    assert data.azione.nsd_kN == pytest.approx(outputs["C22"], rel=1e-5)
    assert data.sismica_en.amax_g == pytest.approx(outputs["C25"], rel=1e-5)
    assert data.azione.ned_kN == pytest.approx(outputs["C26"], rel=1e-4)
    assert data.compressione.ncrd_kN == pytest.approx(outputs["C27"], rel=1e-5)
    assert data.compressione.verifica.passed == _ESITO[outputs["C28"]]
    assert data.compressione.tasso_lavoro == pytest.approx(outputs["C29"], rel=1e-4)
    assert data.trazione.ntrd_kN == pytest.approx(outputs["C30"], rel=1e-5)
    assert data.trazione.verifica.passed == _ESITO[outputs["C31"]]  # sheet bug: compares vs T.L._c
    assert data.trazione.tasso_lavoro == pytest.approx(outputs["C32"], rel=1e-4)
    assert data.snellezza_en.l0_mm == pytest.approx(outputs["C38"], rel=1e-5)
    assert data.snellezza_en.i_mm == pytest.approx(outputs["C39"], rel=1e-4)
    assert data.snellezza_en.omega == pytest.approx(outputs["C40"], rel=1e-4)
    assert data.snellezza_en.lambda_ == pytest.approx(outputs["C41"], rel=1e-4)
    assert data.snellezza_en.lambda_lim == pytest.approx(outputs["C42"], rel=1e-4)
    assert data.snellezza_en.verifica.passed == _ESITO[outputs["C43"]]
    assert data.snellezza_en.tasso_lavoro == pytest.approx(outputs["C44"], rel=1e-4)
    assert data.minimi_en.armatura_longitudinale.rho_b_mm2 == pytest.approx(outputs["C47"], rel=1e-5)
    assert data.minimi_en.armatura_longitudinale.verifica.passed == _ESITO[outputs["C48"]]
    assert data.minimi_en.geometria.bw_min_mm == pytest.approx(outputs["C50"], rel=1e-5)
    assert data.minimi_en.geometria.verifica_base.passed == _ESITO[outputs["C51"]]
    assert data.minimi_en.geometria.hw_min_mm == pytest.approx(outputs["C52"], rel=1e-5)
    assert data.minimi_en.geometria.verifica_altezza.passed == _ESITO[outputs["C53"]]
    assert data.minimi_en.staffe.rho_min == pytest.approx(outputs["C63"], rel=1e-3)
    assert data.minimi_en.staffe.rho == pytest.approx(outputs["C64"], rel=1e-4)
    assert data.minimi_en.staffe.verifica.passed == _ESITO[outputs["C65"]]

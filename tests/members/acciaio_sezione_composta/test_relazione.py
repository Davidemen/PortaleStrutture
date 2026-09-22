"""`relazione.py` (docs/architecture-phase2.md §6, wave-2 adoption): the harness on the tool's own
example and on every oracle input set of `test_oracle.py` (`acciaio_sezione_composta_oracle.json` +
`..._rev00_oracle.json`) — run here in STANDARD mode, since `relazione` only describes the
code-standard branch (docs/architecture-phase2.md §1) and both fixtures were recorded with
`legacy_compat=True` — plus variations that switch branches: the full `MAX_PIATTI=10` fill-down (the
oracle set never exceeds 2 plates), no plates at all (bare profile), and an ODD plate count (3,
exercising the alternating-side stacking of `elementi.elementi_piatti_generale` beyond a simple
symmetric pair).

This tool declares NO `Check` (`tool.py::run` calls `success(data, inputs)` with no `checks=`).
"""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.members.acciaio_sezione_composta.tool import TOOLS
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "acciaio-sezione-h-rimpiattata")

_FIXTURES = Path(__file__).parents[2] / "fixtures"
_REV01_FIXTURE = json.loads((_FIXTURES / "acciaio_sezione_composta_oracle.json").read_text(encoding="utf-8"))
_REV00_FIXTURE = json.loads((_FIXTURES / "acciaio_sezione_composta_rev00_oracle.json").read_text(encoding="utf-8"))


def _raw_from_outputs(outputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "h_profilo_mm": outputs["B1"], "b_profilo_mm": outputs["B2"], "tf_mm": outputs["C6"], "tw_mm": outputs["B7"],
        "piatti": [{"b_mm": outputs["B9"], "h_mm": outputs["C9"]}, {"b_mm": outputs["B10"], "h_mm": outputs["C10"]}],
    }


VARIAZIONI = {
    "dieci_piatti_max_piatti": {
        "h_profilo_mm": 200.0, "b_profilo_mm": 150.0, "tf_mm": 10.0, "tw_mm": 6.0,
        "piatti": [{"b_mm": 6.0 + i, "h_mm": 180.0} for i in range(10)],
    },
    "nessun_piatto_profilo_nudo": {"h_profilo_mm": 200.0, "b_profilo_mm": 150.0, "tf_mm": 10.0, "tw_mm": 6.0, "piatti": []},
    "tre_piatti_lati_alternati": {
        "h_profilo_mm": 160.0, "b_profilo_mm": 140.0, "tf_mm": 10.0, "tw_mm": 6.0,
        "piatti": [{"b_mm": 10.0, "h_mm": 101.0}, {"b_mm": 8.0, "h_mm": 101.0}, {"b_mm": 6.0, "h_mm": 101.0}],
    },
}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _REV01_FIXTURE, ids=range(len(_REV01_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo_rev01(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _raw_from_outputs(case["outputs"]))


@pytest.mark.oracle
def test_relazione_coerente_sul_caso_oracolo_rev00():
    assert_relazione_coerente(TOOL, _raw_from_outputs(_REV00_FIXTURE[0]["outputs"]))


@pytest.mark.parametrize("raw", VARIAZIONI.values(), ids=VARIAZIONI.keys())
def test_relazione_coerente_sulle_variazioni(raw):
    assert_relazione_coerente(TOOL, raw)


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_nessun_check_dichiarato():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.checks == ()


def test_area_formula_ha_tanti_termini_quanti_elementi_attivi():
    """La formula di A deve avere esattamente un termine per elemento realmente presente
    (docs/architecture-phase2.md: nessun valore comparso dal nulla, nessun termine mancante)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_a = next(p for t in report.relazione for p in t.passi if p.simbolo == "A")
    assert len(passo_a.valori) == len(report.data.elementi)


def test_z_pl_dichiara_il_metodo_di_bisezione():
    """W_pl non ha una formula chiusa: la nota deve dirlo esplicitamente, non lasciare il valore
    apparire dal nulla."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "z_pl,x")
    assert "bisezione" in passo.nota


def test_dieci_piatti_ha_tredici_elementi_e_resta_nel_budget():
    raw = VARIAZIONI["dieci_piatti_max_piatti"]
    report = execute(TOOL, raw, con_relazione=True)
    assert len(report.data.elementi) == 13
    totale = sum(len(t.passi) for t in report.relazione)
    assert totale == 17  # 2 Traccia fisse, indipendenti dal numero di elementi

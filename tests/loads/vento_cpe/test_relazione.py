"""`relazione.py` (docs/architecture-phase2.md §6, wave-3 adoption): the harness on the tool's own
example, on the golden-case input of `test_golden.py` (identical to the example, kept for explicit
coverage), and on every oracle input set of `test_oracle.py` (`tests/fixtures/vento_cpe_oracle.json`
— includes h/d > 5 "ND" cases for one or both directions), run in STANDARD mode (the fixture's own
`legacy_compat=True` is never set, `relazione` only describes standard mode,
docs/architecture-phase2.md §1), plus dedicated variations that switch branches: each face's two
linear segments and the fully-slender (both directions "ND") case."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.loads.vento_cpe.tool import TOOLS
from strutture.shared.tool import execute
from tests.loads.vento_cpe.test_golden import GOLDEN_KWARGS
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]

_ORACLE_FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "vento_cpe_oracle.json").read_text())


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    """`test_oracle.py`'s own column mapping, WITHOUT `legacy_compat` (defaults to False/standard)."""
    inp = case["inputs"]
    return {"b": inp["D6"], "d": inp["D7"], "h": inp["D8"]}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden():
    assert_relazione_coerente(TOOL, GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FIXTURE, ids=range(len(_ORACLE_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FIXTURE, ids=range(len(_ORACLE_FIXTURE)))
def test_ogni_highlight_e_spiegato_sui_casi_oracolo(case: dict[str, Any]):
    assert_ogni_highlight_e_spiegato(TOOL, _oracle_raw_inputs(case))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target_on_the_example():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_variazione_entrambe_le_direzioni_snelle_nessun_cpe():
    """h/d > 5 in entrambe le direzioni: nessun coefficiente di pressione è definito (ND); restano
    solo i due passi h/d, e la classificazione nel titolo della seconda Traccia riflette "snello"."""
    variazione = {"b": 10, "d": 10, "h": 60}
    assert_relazione_coerente(TOOL, variazione)
    report = execute(TOOL, variazione, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert totale == 2
    assert "snello" in report.relazione[1].titolo.lower()


def test_variazione_sopravento_tratto_capped():
    """h/d > 1: c_pe sopravento resta al valore massimo costante (0,8), non sulla rampa lineare."""
    variazione = {"b": 4, "d": 4, "h": 20}
    assert_relazione_coerente(TOOL, variazione)
    report = execute(TOOL, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("c_pe,sopravento"))
    assert passo.risultato == pytest.approx(0.8)


def test_variazione_laterale_tratto_rampa():
    """h/d ≤ 0,5: c_pe laterale è ancora sulla rampa lineare, non al valore minimo costante."""
    variazione = {"b": 4, "d": 40, "h": 2}
    assert_relazione_coerente(TOOL, variazione)
    report = execute(TOOL, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("c_pe,laterale (direzione 1"))
    assert passo.risultato != pytest.approx(-0.9)


def test_variazione_sottovento_secondo_tratto():
    """h/d > 1: c_pe sottovento usa il secondo tratto lineare, con la sua stessa pendenza."""
    variazione = {"b": 4, "d": 4, "h": 20}
    assert_relazione_coerente(TOOL, variazione)
    report = execute(TOOL, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("c_pe,sottovento"))
    assert "hd_bp" in {v.simbolo for v in passo.valori}

"""`relazione.py` (docs/architecture-phase2.md §6, wave-3 adoption): the harness on both tools' own
examples, on every golden/oracle input set the package's own tests already use (`test_golden.py`,
`test_oracle_carico_falda.py`, `test_oracle_accumulo.py` — all recorded `legacy_compat=True`;
`relazione` only describes the code-standard branch, docs/architecture-phase2.md §1, so every reused
fixture is fed back with the flag flipped), plus dedicated variations that switch branches: due
falde, parapetto presente, l'angolo di scivolamento sotto/sopra soglia, la costruzione più bassa non
più stretta della zona di accumulo, e la formula di q_sk in funzione della quota."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.loads.neve.tool import TOOLS
from strutture.shared.tool import execute
from tests.loads.neve.test_golden import ACCUMULO_GOLDEN_KWARGS, FALDA_GOLDEN_KWARGS
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL_FALDA = next(t for t in TOOLS if t.name == "neve-carico-falda")
TOOL_ACCUMULO = next(t for t in TOOLS if t.name == "neve-accumulo")

_ORACLE_FALDA = json.loads((Path(__file__).parents[2] / "fixtures" / "neve_carico_falda_oracle.json").read_text())
_ORACLE_ACCUMULO = json.loads((Path(__file__).parents[2] / "fixtures" / "neve_accumulo_oracle.json").read_text())


def _oracle_falda_raw(case: dict[str, Any]) -> dict[str, Any]:
    """`test_oracle_carico_falda.py`'s own column mapping, WITHOUT `legacy_compat` (defaults to
    False/standard — `relazione` never runs in legacy mode). Both roof-type blocks always given
    (the oracle sheet always computes both), `tipo_copertura` forced to "due falde" as the source
    test does."""
    inp = case["inputs"]
    return {
        "comune": inp["H5"], "as_m": inp["H9"], "topografia": inp["H13"], "ct": inp["H26"],
        "tipo_copertura": "Copertura a due falde",
        "a": inp["H30"], "parapetto": inp["H31"], "a1": inp["H52"], "parapetto1": inp["H53"],
        "a2": inp["H56"], "parapetto2": inp["H57"],
    }


def _oracle_accumulo_raw(case: dict[str, Any]) -> dict[str, Any]:
    """`test_oracle_accumulo.py`'s own column mapping, WITHOUT `legacy_compat`."""
    inp = case["inputs"]
    return {
        "comune": inp["H5"], "as_m": inp["H9"], "topografia": inp["H13"], "ct": inp["H26"],
        "b1": inp["H29"], "b2": inp["H30"], "h": inp["H31"], "gamma": inp["H32"], "a": inp["H34"],
        "m1_input": inp["H35"], "msup": inp["H37"], "neve_sheet_as_m": inp["neve_h9"],
    }


def test_tools_declare_relazione():
    assert TOOL_FALDA.relazione is not None
    assert TOOL_ACCUMULO.relazione is not None


def test_relazione_coerente_sugli_esempi():
    assert_relazione_coerente(TOOL_FALDA, TOOL_FALDA.example)
    assert_relazione_coerente(TOOL_ACCUMULO, TOOL_ACCUMULO.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_una_falda():
    assert_relazione_coerente(TOOL_FALDA, {**FALDA_GOLDEN_KWARGS, "tipo_copertura": "Copertura ad una falda"})


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_due_falde():
    assert_relazione_coerente(TOOL_FALDA, {**FALDA_GOLDEN_KWARGS, "tipo_copertura": "Copertura a due falde"})


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_accumulo():
    assert_relazione_coerente(TOOL_ACCUMULO, ACCUMULO_GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FALDA, ids=range(len(_ORACLE_FALDA)))
def test_relazione_coerente_sui_casi_oracolo_falda(case: dict[str, Any]):
    assert_relazione_coerente(TOOL_FALDA, _oracle_falda_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_ACCUMULO, ids=range(len(_ORACLE_ACCUMULO)))
def test_relazione_coerente_sui_casi_oracolo_accumulo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL_ACCUMULO, _oracle_accumulo_raw(case))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL_FALDA, TOOL_FALDA.example)
    assert_ogni_highlight_e_spiegato(TOOL_ACCUMULO, TOOL_ACCUMULO.example)


def test_ogni_highlight_e_spiegato_due_falde():
    """`qs1`/`qs2` (non `qs`) sono gli highlight quando `tipo_copertura` è "due falde"."""
    variazione = {**TOOL_FALDA.example, "tipo_copertura": "Copertura a due falde"}
    assert_ogni_highlight_e_spiegato(TOOL_FALDA, variazione)


def test_step_count_within_the_8_to_30_target():
    for tool in (TOOL_FALDA, TOOL_ACCUMULO):
        report = execute(tool, tool.example, con_relazione=True)
        totale = sum(len(t.passi) for t in report.relazione)
        assert 8 <= totale <= 30, f"{tool.name}: {totale} passi"


def test_variazione_parapetto_presente():
    """Con barriera al bordo inferiore, μ resta al valore massimo indipendentemente dall'angolo:
    il passo diventa una pura lettura da tabella (formula = identificatore stesso)."""
    variazione = {**TOOL_FALDA.example, "parapetto": "SI", "a": 45}
    assert_relazione_coerente(TOOL_FALDA, variazione)
    report = execute(TOOL_FALDA, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ")
    assert passo.formula == "μ_max"


def test_variazione_qsk_formula_in_quota():
    """Altitudine > 200 m: q_sk segue la formula in funzione della quota, non il valore costante."""
    variazione = {**TOOL_FALDA.example, "as_m": 800}
    assert_relazione_coerente(TOOL_FALDA, variazione)
    report = execute(TOOL_FALDA, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "q_sk")
    assert "a_s" in {v.simbolo for v in passo.valori}


def _passo_mu_s(report):
    return next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("μ_s"))


def test_variazione_scivolamento_sotto_soglia():
    """Angolo della falda più alta < 15°: nessun contributo da scivolamento (μ_s=0)."""
    variazione = {**TOOL_ACCUMULO.example, "a": 5}
    assert_relazione_coerente(TOOL_ACCUMULO, variazione)
    report = execute(TOOL_ACCUMULO, variazione, con_relazione=True)
    passo = _passo_mu_s(report)
    assert passo.formula == "0"
    assert passo.risultato == pytest.approx(0.0)


def test_variazione_scivolamento_sopra_soglia():
    """Angolo della falda più alta ≥ 15°: μ_s = μ_sup/2."""
    variazione = {**TOOL_ACCUMULO.example, "a": 20}
    assert_relazione_coerente(TOOL_ACCUMULO, variazione)
    report = execute(TOOL_ACCUMULO, variazione, con_relazione=True)
    passo = _passo_mu_s(report)
    assert passo.formula == "μ_sup / 2"


def test_mu_s_riporta_la_condizione_sullangolo_nel_simbolo():
    """review finding MISSING_STEP: `traccia_a_testo` non stampa mai `Passo.nota` — 'μ_s = 0'
    stampato senza condizione si legge come una legge incondizionata, non come l'esito del solo
    ramo α < 15° (accumulo_ms.py restituisce μ_sup/2 quando α ≥ 15°)."""
    sotto = execute(TOOL_ACCUMULO, {**TOOL_ACCUMULO.example, "a": 5}, con_relazione=True)
    sopra = execute(TOOL_ACCUMULO, {**TOOL_ACCUMULO.example, "a": 20}, con_relazione=True)
    assert _passo_mu_s(sotto).simbolo != "μ_s"
    assert _passo_mu_s(sotto).simbolo != _passo_mu_s(sopra).simbolo


def test_variazione_b2_non_minore_di_ls():
    """L'esempio del tool (b_2=36,2 m ≥ l_s=15 m): la costruzione più bassa non è più stretta
    della zona di accumulo, μ_1,final resta il valore imposto in ingresso (nessuna interpolazione)."""
    report = execute(TOOL_ACCUMULO, TOOL_ACCUMULO.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ_1,final")
    assert passo.formula == "μ_1,imp"


def test_variazione_b2_minore_di_ls_interpola():
    """La costruzione più bassa è più stretta della zona di accumulo (b_2=10 m < l_s=15 m):
    μ_1,final è interpolato tra μ_w e μ_1,imp."""
    variazione = {**TOOL_ACCUMULO.example, "b2": 10}
    assert_relazione_coerente(TOOL_ACCUMULO, variazione)
    report = execute(TOOL_ACCUMULO, variazione, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ_1,final")
    assert passo.formula != "μ_1,imp"
    assert {"μ_w", "l_s"} <= {v.simbolo for v in passo.valori}

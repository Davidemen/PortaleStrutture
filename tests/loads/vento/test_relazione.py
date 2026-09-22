"""`relazione.py` (docs/architecture-phase2.md §6, wave-3 adoption): the harness on the tool's own
example, on the golden-case input of `test_golden.py`, and on every oracle input set of
`test_oracle.py` (`tests/fixtures/vento_pressione_oracle.json`) — run here in STANDARD mode (the
fixture's own `legacy_compat=True` is never set, `relazione` only describes standard mode,
docs/architecture-phase2.md §1), plus dedicated variations that switch branches: altitude above/at
the zone's own threshold a_0 (c_a formula vs constant)."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.loads.vento.tool import TOOLS
from strutture.shared.tool import execute
from tests.loads.vento.test_golden import GOLDEN_KWARGS
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]

_ORACLE_FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "vento_pressione_oracle.json").read_text())

# Case 5 (Genova, a_s=2000 m) is excluded from the STANDARD-mode oracle parametrization below:
# NTC2018 §3.3.2 bars extrapolation above 1500 m in standard mode (`vref.py::coefficiente_altitudine`
# raises `CalcError`, docs/divergences/vento.md) — the sheet's own legacy-mode extrapolation past
# that limit has no standard-mode equivalent for `relazione` (which never describes legacy mode) to
# restate.
_CASO_OLTRE_LIMITE_ALTITUDINE = 5
_ORACLE_CASI_STANDARD = [
    (i, case) for i, case in enumerate(_ORACLE_FIXTURE) if i != _CASO_OLTRE_LIMITE_ALTITUDINE
]


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    """`test_oracle.py`'s own column mapping, WITHOUT `legacy_compat` (defaults to False/standard)."""
    inp = case["inputs"]
    return {
        "comune": inp["H4"], "altitudine_m": inp["H8"], "periodo_ritorno_anni": inp["H13"],
        "categoria_esposizione": inp["H29"], "ct": inp["H33"], "altezza_edificio_m": inp["H34"],
        "n_sezioni": 1000,
    }


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden():
    assert_relazione_coerente(TOOL, GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", [c for _, c in _ORACLE_CASI_STANDARD], ids=[i for i, _ in _ORACLE_CASI_STANDARD])
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(case))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def _passo_ca(report):
    return next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("c_a"))


def test_variazione_altitudine_sopra_a0():
    """a_s > a_0 della zona (1000 m, zona 1 di Milano): c_a segue la formula di correzione
    lineare, non resta a 1."""
    variazione = {**TOOL.example, "altitudine_m": 1200}
    assert_relazione_coerente(TOOL, variazione)
    report = execute(TOOL, variazione, con_relazione=True)
    passo = _passo_ca(report)
    assert passo.formula != "1"
    assert passo.risultato != pytest.approx(1.0)


def test_variazione_altitudine_al_massimo_ammesso():
    """a_s pari al limite di 1500 m: ancora ammesso in modalità standard (nessun CalcError)."""
    variazione = {**TOOL.example, "altitudine_m": 1500}
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_altitudine_sotto_o_uguale_a0():
    """L'esempio del tool (a_s=120 m ≤ a_0=1000 m della zona 1): c_a resta costante a 1."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = _passo_ca(report)
    assert passo.formula == "1"
    assert passo.risultato == pytest.approx(1.0)


def test_c_a_riporta_la_condizione_che_lo_governa_nel_simbolo_stampato():
    """`traccia_a_testo` non stampa mai `Passo.nota` (docs/architecture-phase2.md, review finding
    MISSING_STEP condiviso da neve/vento/ca_fessurazione/acciaio_colonna_ec3/ca_sezione_mn): la
    condizione a_s ≤ a_0 / a_s > a_0 che seleziona la formula di c_a deve comparire nel simbolo
    stampato, non solo nella nota invisibile."""
    report_sotto = execute(TOOL, TOOL.example, con_relazione=True)  # a_s=120 <= a_0=1000
    report_sopra = execute(TOOL, {**TOOL.example, "altitudine_m": 1200}, con_relazione=True)
    assert "a_s" in _passo_ca(report_sotto).simbolo and "a_0" in _passo_ca(report_sotto).simbolo
    assert _passo_ca(report_sotto).simbolo != _passo_ca(report_sopra).simbolo


def _passo(report, simbolo: str):
    return next(p for t in report.relazione for p in t.passi if p.simbolo == simbolo)


def test_pressione_cinetica_e_chiamata_qr_non_qb():
    """La pressione cinetica costruita su v_r (non v_b) non può chiamarsi q_b (simbolo di
    EN1991-1-4 = 0,5·ρ·v_b²): deve chiamarsi q_r, come in NTC2018, citando §3.3.6 (review
    finding WRONG_CLAUSE su loads/vento)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = _passo(report, "q_r")
    assert passo.clausola == "NTC2018 §3.3.6"
    assert not any(p.simbolo == "q_b" for t in report.relazione for p in t.passi)


def test_p_h_mostra_cp_e_cd_e_cita_3_3_4():
    """p(H) è l'unico simbolo esplicitato nell'output (highlight): deve restare tale, ma la
    formula stampata deve mostrare c_p e c_d (NTC2018 §3.3.4: p = q_r·c_e·c_p·c_d), non
    scomparire dietro 'q_b·c_eH' sotto la clausola sbagliata."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = _passo(report, "p(H)")
    assert passo.clausola == "NTC2018 §3.3.4"
    assert "c_p" in passo.formula and "c_d" in passo.formula


def test_c_r_cita_ntc2018_non_la_circolare():
    """periodo_ritorno.py chiama l'equazione '(Vento!H14, NTC2018 eq. 3.3.3)': la traccia non può
    citare 'Circ. NTC2019 §C3.3.2', un documento diverso con una numerazione diversa (review
    finding WRONG_CLAUSE)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = _passo(report, "c_r")
    assert passo.clausola == "NTC2018 §3.3.2 eq. (3.3.3)"
    assert "Circ" not in passo.clausola


def test_c_a_cita_3_3_1_come_v_b0_a_0_k_s():
    """v_b = v_b,0·c_a e Tab. 3.3.I sono introdotti in §3.3.1, non in §3.3.2 (review finding
    WRONG_CLAUSE): c_a deve condividere la clausola di v_b,0/a_0/k_s."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_ca = _passo_ca(report)
    passo_vb0 = _passo(report, "v_b,0")
    assert passo_ca.clausola == passo_vb0.clausola == "NTC2018 §3.3.1 Tab. 3.3.I"

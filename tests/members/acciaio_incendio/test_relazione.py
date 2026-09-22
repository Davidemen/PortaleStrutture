"""`relazione.py` (docs/architecture-phase2.md §6, wave-2 adoption) for BOTH tools of this package
(`acciaio-resistenza-incendio`, `acciaio-proprieta-temperatura`): the harness on each tool's own
example and on every golden/oracle input set the package's own tests already use — run here in
STANDARD mode (`relazione` only describes the code-standard branch, docs/architecture-phase2.md §1);
`proprieta.py`'s own docstring notes `legacy_compat` has no numeric effect on that tool at all, so
its oracle fixture is safe to replay unchanged — plus variations that switch branches: the full
default 24-row `tempi_min` fill-down (vs. the tool's own single-row example) and the S275 grade
(the `fu_20_MPa` divergence, invisible here since `relazione` never runs `legacy_compat=True`, but a
different table row nonetheless).

Neither tool declares a `Check` (`tool.run`/`proprieta_tool.run` call `success(...)` with no
`checks=`): there is nothing to cover beyond the highlighted outputs.
"""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.members.acciaio_incendio.models import DEFAULT_TEMPI_MIN
from strutture.members.acciaio_incendio.proprieta_tool import TOOLS as PROPRIETA_TOOLS
from strutture.members.acciaio_incendio.tool import TOOLS as RESISTENZA_TOOLS
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL_RESISTENZA = next(t for t in RESISTENZA_TOOLS if t.name == "acciaio-resistenza-incendio")
TOOL_PROPRIETA = next(t for t in PROPRIETA_TOOLS if t.name == "acciaio-proprieta-temperatura")

_FIXTURES = Path(__file__).parents[2] / "fixtures"
_RESISTENZA_FIXTURE = json.loads((_FIXTURES / "acciaio_incendio_resistenza_oracle.json").read_text(encoding="utf-8"))
_PROPRIETA_FIXTURE = json.loads((_FIXTURES / "acciaio_incendio_proprieta_oracle.json").read_text(encoding="utf-8"))


def _resistenza_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    return {"grado": case["inputs"]["D2"].upper(), "e_20_MPa": float(case["inputs"]["D3"]), "tempi_min": (5.0, 120.0)}


def _proprieta_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    outputs = case["outputs"]
    return {"fyk_MPa": float(outputs["C20"]), "ea_20_MPa": float(outputs["C21"]), "theta_C": float(outputs["C22"])}


def test_tools_declare_relazione():
    assert TOOL_RESISTENZA.relazione is not None
    assert TOOL_PROPRIETA.relazione is not None


def test_relazione_coerente_sugli_esempi():
    assert_relazione_coerente(TOOL_RESISTENZA, TOOL_RESISTENZA.example)
    assert_relazione_coerente(TOOL_PROPRIETA, TOOL_PROPRIETA.example)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _RESISTENZA_FIXTURE, ids=range(len(_RESISTENZA_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo_resistenza(case: dict[str, Any]):
    assert_relazione_coerente(TOOL_RESISTENZA, _resistenza_oracle_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _PROPRIETA_FIXTURE, ids=lambda c: c["sheet"])
def test_relazione_coerente_sui_casi_oracolo_proprieta(case: dict[str, Any]):
    assert_relazione_coerente(TOOL_PROPRIETA, _proprieta_oracle_raw(case))


def test_variazione_fill_down_completo_24_righe():
    """La traccia deve restare coerente e tracciare la riga governante (t=120 min) anche quando
    sono richieste tutte le 24 righe di fill-down di default."""
    raw = {"grado": "S355", "tempi_min": DEFAULT_TEMPI_MIN}
    assert_relazione_coerente(TOOL_RESISTENZA, raw)
    report = execute(TOOL_RESISTENZA, raw, con_relazione=True)
    assert "t=120 min" in report.relazione[0].titolo


def test_variazione_grado_s275():
    """S275 (colonna della tabella EN10025 diversa da quella dell'esempio, S355)."""
    assert_relazione_coerente(TOOL_RESISTENZA, {"grado": "S275", "tempi_min": (30.0,)})


def test_variazione_theta_su_nodo_tabellare():
    """θ=600°C cade esattamente su un nodo di Tab. 3.1 (non richiede interpolazione fra nodi)."""
    assert_relazione_coerente(TOOL_PROPRIETA, {"fyk_MPa": 355.0, "ea_20_MPa": 210000.0, "theta_C": 600.0})


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL_RESISTENZA, TOOL_RESISTENZA.example)
    assert_ogni_highlight_e_spiegato(TOOL_PROPRIETA, TOOL_PROPRIETA.example)


def test_nessun_check_dichiarato_da_nessuno_dei_due_tool():
    for tool in (TOOL_RESISTENZA, TOOL_PROPRIETA):
        report = execute(tool, tool.example, con_relazione=True)
        assert report.checks == ()


def test_fu_theta_riusa_k_y_theta_e_lo_dice():
    """review finding WRONG_CLAUSE: EN1993-1-2 §3.2.1/Tab. 3.1 definiscono solo k_y,θ/k_p,θ/k_E,θ
    (bulloni e saldature sono nell'Annex D): non esiste un k_u,θ per i profili, quindi la riga non
    può citare '§3.2.1' come se fosse una clausola normativa. `Passo.clausola` (non solo `nota`,
    che `traccia_a_testo` non stampa mai) deve dichiarare l'ipotesi in chiaro."""
    report = execute(TOOL_RESISTENZA, TOOL_RESISTENZA.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "f_u,θ")
    assert passo.clausola != "EN1993-1-2 §3.2.1"
    assert "ipotesi" in passo.clausola.lower()
    assert "k_y,θ" in passo.clausola


def test_theta_cita_leq_3_4_non_lallegato_a_curva_parametrica():
    """review finding WRONG_CLAUSE: Θg=20+345·log10(8t+1) è la curva nominale ISO 834, EN1991-1-2
    §3.2.1 eq. (3.4); l'Annex A eq. (A.1) è la curva PARAMETRICA (Θg=20+1325(1-0,324e^-0,2t*-…)),
    un modello diverso — la didascalia 'curva nominale ISO 834' contraddiceva la clausola citata."""
    report = execute(TOOL_RESISTENZA, TOOL_RESISTENZA.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "θ")
    assert "Annex A" not in passo.clausola
    assert "eq. (3.4)" in passo.clausola
    assert "§3.2.1" in passo.clausola

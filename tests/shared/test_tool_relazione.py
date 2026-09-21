"""`execute(..., con_relazione=True)` and the failure discipline of docs/architecture-phase2.md §1:
a failing trace NEVER fails the calculation, and every existing caller keeps working unchanged."""
import pytest
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.relazione.modelli import Passo, Traccia, Valore
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tool import (
    AVVISO_RELAZIONE_MODALITA_EXCEL,
    AVVISO_RELAZIONE_NON_DISPONIBILE,
    Tool,
    execute,
)

pytestmark = pytest.mark.unit


class SommaIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    a: float = Field(default=1.0)
    b: float = Field(default=2.0)
    legacy_compat: bool = False


class SommaOut(BaseModel):
    model_config = ConfigDict(frozen=True)
    totale: float


def _run(inputs: SommaIn) -> Report[SommaOut]:
    if inputs.a < 0:
        raise CalcError("a deve essere non negativo")
    return success(SommaOut(totale=inputs.a + inputs.b), inputs)


def _traccia_ok(inputs: SommaIn, output: SommaOut) -> tuple[Traccia, ...]:
    passo = Passo(
        simbolo="totale", formula="a + b",
        valori=(Valore(simbolo="a", valore=inputs.a), Valore(simbolo="b", valore=inputs.b)),
        risultato=output.totale,
    )
    return (Traccia(titolo="Somma", passi=(passo,)),)


def _traccia_rompe(inputs: SommaIn, output: SommaOut) -> tuple[Traccia, ...]:
    raise RuntimeError("bug simulato nella relazione")


TOOL_CON_RELAZIONE = Tool("somma", "Somma", "Test", "-", SommaIn, SommaOut, _run, relazione=_traccia_ok)
TOOL_RELAZIONE_ROTTA = Tool("somma-rotta", "Somma rotta", "Test", "-", SommaIn, SommaOut, _run, relazione=_traccia_rompe)
TOOL_SENZA_RELAZIONE = Tool("somma-nuda", "Somma nuda", "Test", "-", SommaIn, SommaOut, _run)


def test_existing_callers_without_con_relazione_are_unaffected():
    report = execute(TOOL_CON_RELAZIONE, {"a": 1, "b": 2})
    assert report.ok and report.relazione == () and report.warnings == ()


def test_con_relazione_true_builds_the_trace_on_a_successful_run():
    report = execute(TOOL_CON_RELAZIONE, {"a": 1, "b": 2}, con_relazione=True)
    assert report.ok
    assert len(report.relazione) == 1
    assert report.relazione[0].passi[0].risultato == pytest.approx(3.0)
    assert report.warnings == ()


def test_con_relazione_true_but_tool_has_no_relazione_is_a_no_op():
    report = execute(TOOL_SENZA_RELAZIONE, {"a": 1, "b": 2}, con_relazione=True)
    assert report.ok and report.relazione == () and report.warnings == ()


def test_con_relazione_true_on_a_failed_run_never_calls_relazione():
    report = execute(TOOL_CON_RELAZIONE, {"a": -1, "b": 2}, con_relazione=True)
    assert not report.ok and report.relazione == ()


def test_a_failing_trace_never_fails_the_calculation():
    report = execute(TOOL_RELAZIONE_ROTTA, {"a": 1, "b": 2}, con_relazione=True)
    assert report.ok  # the calculation itself is untouched
    assert report.data.totale == pytest.approx(3.0)
    assert report.relazione == ()
    assert report.warnings == (AVVISO_RELAZIONE_NON_DISPONIBILE,)


def test_excel_mode_never_gets_a_trace_even_if_relazione_would_succeed():
    report = execute(TOOL_CON_RELAZIONE, {"a": 1, "b": 2, "legacy_compat": True}, con_relazione=True)
    assert report.ok
    assert report.relazione == ()
    assert report.warnings == (AVVISO_RELAZIONE_MODALITA_EXCEL,)


def test_relazione_never_mutates_the_original_report_object():
    """Immutability: `execute` returns a NEW Report; nothing about the plain run is mutated in place."""
    plain = execute(TOOL_CON_RELAZIONE, {"a": 1, "b": 2})
    with_relazione = execute(TOOL_CON_RELAZIONE, {"a": 1, "b": 2}, con_relazione=True)
    assert plain.relazione == () and with_relazione.relazione != ()

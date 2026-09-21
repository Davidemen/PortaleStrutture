"""Test harness for `relazione` (docs/architecture-phase2.md §4): every trace a tool declares must
reproduce, from its own formula and values, the numbers the tool actually computed. Not a
`test_*.py` file on purpose — pytest never collects it; both the global tests
(`test_harness_globale.py`) and each adopting package's own tests import `assert_relazione_coerente`
directly, the way `docs/architecture-phase2.md` §6 expects every adoption wave to.
"""
from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import BaseModel

from strutture.shared.relazione.modelli import Traccia
from strutture.shared.relazione.verifica import problemi_traccia
from strutture.shared.tool import Tool, execute

TOLLERANZA_RELATIVA = 1e-6
TOLLERANZA_ASSOLUTA = 1e-9


def assert_relazione_coerente(tool: Tool, raw_inputs: dict[str, Any]) -> None:
    """Run `tool` on `raw_inputs` with `con_relazione=True` and assert the resulting `relazione`
    is fully coherent with §4: every formula parses and evaluates to its own `risultato`, every
    check's `esito`/`clausola` matches, and every `risultato`/`unita` that names an output field
    (same `symbol` hint) matches that field."""
    report = execute(tool, raw_inputs, con_relazione=True)
    assert report.ok, f"{tool.name}: run failed on {raw_inputs!r}: {report.errors}"
    assert report.relazione, f"{tool.name}: con_relazione=True produced no trace (warnings={report.warnings!r})"
    problemi = problemi_traccia(report.relazione)
    assert not problemi, f"{tool.name}: {problemi}"
    _assert_coerente_con_output(tool, report.relazione, report.data)


def assert_ogni_highlight_e_spiegato(tool: Tool, raw_inputs: dict[str, Any]) -> None:
    """Second global check of §4: every `highlight` output symbol of `tool` appears as some
    `Passo.simbolo` in its `relazione` for `raw_inputs`."""
    report = execute(tool, raw_inputs, con_relazione=True)
    assert report.ok, f"{tool.name}: run failed on {raw_inputs!r}: {report.errors}"
    mancanti = _simboli_evidenziati(report.data) - _simboli_dei_passi(report.relazione)
    assert not mancanti, f"{tool.name}: highlight non spiegati da alcun Passo: {sorted(mancanti)}"


def _assert_coerente_con_output(tool: Tool, tracce: tuple[Traccia, ...], output: BaseModel) -> None:
    valori_output = dict(_valori_simbolo(output))
    for traccia in tracce:
        for passo in traccia.passi:
            if passo.simbolo not in valori_output:
                continue
            valore, unita = valori_output[passo.simbolo]
            assert passo.risultato == pytest.approx(valore, rel=TOLLERANZA_RELATIVA, abs=TOLLERANZA_ASSOLUTA), (
                f"{tool.name}/{passo.simbolo}: risultato={passo.risultato} != output {valore}"
            )
            if unita:
                assert passo.unita, f"{tool.name}/{passo.simbolo}: manca unita (l'output ha {unita!r})"


def _simboli_dei_passi(tracce: tuple[Traccia, ...]) -> frozenset[str]:
    return frozenset(passo.simbolo for traccia in tracce for passo in traccia.passi)


def _simboli_evidenziati(output: BaseModel) -> frozenset[str]:
    return frozenset(simbolo for simbolo, _, evidenziato in _campi_output(output) if evidenziato)


def _valori_simbolo(output: BaseModel) -> Iterator[tuple[str, tuple[float, str]]]:
    for simbolo, (valore, unita), _ in _campi_output(output):
        yield simbolo, (valore, unita)


def _campi_output(modello: BaseModel) -> Iterator[tuple[str, tuple[float, str], bool]]:
    """(symbol, (value, unit), highlight) for every numeric leaf field with a `symbol` hint,
    recursing into nested output models. Tuples of rows are not recursed into: §5 traces the
    GOVERNING row only, and a per-row `symbol` would be ambiguous across rows."""
    for nome, campo in type(modello).model_fields.items():
        valore = getattr(modello, nome)
        if isinstance(valore, BaseModel):
            yield from _campi_output(valore)
            continue
        if isinstance(valore, bool) or not isinstance(valore, int | float):
            continue
        estra = campo.json_schema_extra
        simbolo = estra.get("symbol") if isinstance(estra, dict) else None
        if simbolo:
            yield simbolo, (float(valore), estra.get("unit", "")), bool(estra.get("highlight"))

"""Typed links between tools (docs/ROADMAP.md phase 5).

A field declares, in its `json_schema_extra`, `provides: "<chiave>"` (an output field, or an input
field whose value is worth forwarding as it is) or `accepts: "<chiave>"` (an input field). Keys are
`<ambito>.<nome>` in snake case (a unit keeps its own case) and carry their unit in the name (`sito.ag_g`, `trave.sigma_s_rara_MPa`):
the UI never converts, it copies. The registry below resolves who feeds whom; `problemi` is run by a
permanent test so that an `accepts` without provider, a `provides` nobody reads, or an enum value the
consumer cannot take never reach the UI. Rows (`tuple[Model, ...]`) never provide: a link value is
one scalar."""
import re
import types
import typing
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from .tool import Tool

CHIAVE = re.compile(r"^[a-z][a-zA-Z0-9_]*\.[a-z][a-zA-Z0-9_]*$")  # units keep their case: sigma_s_rara_MPa


@dataclass(frozen=True)
class Fornitore:
    strumento: str
    percorso: str  # dotted path in `inputs_echo` (ingresso=True) or in `data`
    ingresso: bool
    valori: frozenset[str] | None = None  # enum choices, None for a number


@dataclass(frozen=True)
class Consumatore:
    strumento: str
    campo: str
    valori: frozenset[str] | None = None


@dataclass(frozen=True)
class Collegamento:
    chiave: str
    fornitori: tuple[Fornitore, ...]
    consumatori: tuple[Consumatore, ...]


def raccogli(tools: Mapping[str, Tool]) -> dict[str, Collegamento]:
    """Every declared key with its providers and consumers, in tool order."""
    fornitori: dict[str, list[Fornitore]] = {}
    consumatori: dict[str, list[Consumatore]] = {}
    for tool in tools.values():
        for campo, extra, valori in _campi(tool.input_model, ""):
            if chiave := extra.get("provides"):
                fornitori.setdefault(chiave, []).append(Fornitore(tool.name, campo, True, valori))
            if chiave := extra.get("accepts"):
                consumatori.setdefault(chiave, []).append(Consumatore(tool.name, campo, valori))
        for percorso, extra, valori in _campi(tool.output_model, ""):
            if chiave := extra.get("provides"):
                fornitori.setdefault(chiave, []).append(Fornitore(tool.name, percorso, False, valori))
    chiavi = sorted(fornitori.keys() | consumatori.keys())
    return {c: Collegamento(c, tuple(fornitori.get(c, ())), tuple(consumatori.get(c, ()))) for c in chiavi}


def valori_forniti(tool: Tool, report_json: Mapping[str, Any]) -> dict[str, Any]:
    """`{chiave: valore}` a run of `tool` offers to its consumers: forwarded inputs always, outputs
    only when the run has data."""
    valori: dict[str, Any] = {}
    echo = report_json.get("inputs_echo") or {}
    data = report_json.get("data") if isinstance(report_json.get("data"), Mapping) else None
    for campo, extra, _ in _campi(tool.input_model, ""):
        if (chiave := extra.get("provides")) and (valore := _leggi(echo, campo)) is not None:
            valori[chiave] = valore
    if data is not None:
        for percorso, extra, _ in _campi(tool.output_model, ""):
            if (chiave := extra.get("provides")) and (valore := _leggi(data, percorso)) is not None:
                valori[chiave] = valore
    return valori


def problemi(tools: Mapping[str, Tool]) -> tuple[str, ...]:
    """Inconsistencies of the registry, as Italian sentences (empty = consistent)."""
    trovati: list[str] = []
    for chiave, link in raccogli(tools).items():
        if not CHIAVE.match(chiave):
            trovati.append(f"chiave {chiave!r} non valida: attesa '<ambito>.<nome>' (snake case, unità con la propria maiuscola)")
        for c in link.consumatori:
            if not link.fornitori:
                trovati.append(f"{chiave}: accettata da {c.strumento}.{c.campo} ma nessuno strumento la fornisce")
        for f in link.fornitori:
            if not link.consumatori:
                trovati.append(f"{chiave}: fornita da {f.strumento}.{f.percorso} ma nessuno strumento la accetta")
            for c in link.consumatori:
                trovati.extend(_incompatibilita(chiave, f, c))
    return tuple(trovati)


def _incompatibilita(chiave: str, f: Fornitore, c: Consumatore) -> Iterator[str]:
    if (f.valori is None) != (c.valori is None):
        yield f"{chiave}: {f.strumento}.{f.percorso} e {c.strumento}.{c.campo} non sono dello stesso tipo (numero / scelta)"
        return
    if f.valori is not None and c.valori is not None:
        for valore in sorted(f.valori - c.valori):
            yield f"{chiave}: {f.strumento}.{f.percorso} fornisce il valore {valore!r} che {c.strumento}.{c.campo} non accetta"


def _campi(model: type[BaseModel], prefisso: str) -> Iterator[tuple[str, dict[str, Any], frozenset[str] | None]]:
    """(dotted path, json_schema_extra, enum choices) of every scalar field, nested models included."""
    for nome, info in model.model_fields.items():
        percorso = f"{prefisso}{nome}"
        annidato = _modello_annidato(info.annotation)
        if annidato is not None:
            yield from _campi(annidato, f"{percorso}.")
            continue
        extra = info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        yield percorso, extra, _scelte(info.annotation)


def _modello_annidato(annotation: Any) -> type[BaseModel] | None:
    """The nested model of a field typed `Model` or `Model | None`; rows (`tuple[Model, ...]`) are not descended."""
    for candidato in _rami(annotation):
        if isinstance(candidato, type) and issubclass(candidato, BaseModel):
            return candidato
    return None


def _scelte(annotation: Any) -> frozenset[str] | None:
    for candidato in _rami(annotation):
        if typing.get_origin(candidato) is typing.Literal:
            return frozenset(str(v) for v in typing.get_args(candidato))
    return None


def _rami(annotation: Any) -> tuple[Any, ...]:
    origine = typing.get_origin(annotation)
    if origine is typing.Union or origine is types.UnionType:
        return tuple(a for a in typing.get_args(annotation) if a is not type(None))
    return (annotation,)


def _leggi(contenitore: Mapping[str, Any], percorso: str) -> Any:
    valore: Any = contenitore
    for parte in percorso.split("."):
        if not isinstance(valore, Mapping) or parte not in valore:
            return None
        valore = valore[parte]
    return valore

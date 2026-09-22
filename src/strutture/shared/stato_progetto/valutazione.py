"""Glue between the pure §25 rules and a running tool: reads a provider's current value at a
`percorso`, so `origini.py` never needs to know about `Tool`/`execute`."""
from collections.abc import Mapping
from typing import Any

from strutture.shared.tool import Tool, execute


def valore_attuale_a_percorso(elemento: Any, percorso: str, ingresso: bool, tools: Mapping[str, Tool]) -> Any:
    """Run `elemento.strumento` with `elemento.inputs` and read `percorso` from `inputs_echo` (an
    input value forwarded as-is) or `data` (a computed output). Raises on an unknown tool or a
    failing run: the caller turns that into "origine non calcolabile"."""
    tool = tools[elemento.strumento]
    report = execute(tool, elemento.inputs)
    if not report.ok:
        raise ValueError(f"il fornitore {elemento.id} non calcola con i dati salvati")
    sorgente = report.inputs_echo if ingresso else (report.data.model_dump(mode="json") if report.data else {})
    return _leggi(sorgente, percorso)


def _leggi(contenitore: Any, percorso: str) -> Any:
    valore = contenitore
    for parte in percorso.split("."):
        if not isinstance(valore, Mapping) or parte not in valore:
            return None
        valore = valore[parte]
    return valore

"""Every sketch text that stands for an INPUT must be editable from the drawing (owner's rule,
2026-09-22, WORKBENCH_SPEC §18): either the UI links it by itself (symbol + unit + shown value equal
the field's) or the sketch names the field with `campo=`. This test mirrors js/schizzo-modifica.js's
matching over every tool's example sketch, so a new tool or a renamed symbol cannot silently leave a
dimension, a label, an arrow text or a diagram text unlinked while an input carries its symbol."""
from __future__ import annotations

import re

import pytest

from strutture.shared.tool import Tool, discover, execute

TESTO_RE = re.compile(r"^(.+?) = ([^ ]+)(?: (.+))?$")


def _unita(unit: str | None) -> str:
    return (unit or "").replace("²", "2").replace("³", "3").strip()


def _numero(testo: str) -> float | None:
    try:
        return float(testo.replace(".", "").replace(",", ".")) if "," in testo else float(testo)
    except ValueError:
        return None


def _campi_numerici(tool: Tool) -> dict[str, tuple[str, str, float | None]]:
    """name -> (symbol, unit, example value) for every number input."""
    out = {}
    for name, field in tool.input_model.model_fields.items():
        extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
        value = (tool.example or {}).get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out[name] = (extra.get("symbol") or "", _unita(extra.get("unit")), float(value))
    return out


def _testi(forma) -> list[tuple[str, str | None]]:
    """(text as the UI composes it, explicit campo) for every text-bearing shape."""
    if forma.kind == "dimension":
        return [(forma.testo, forma.campo)]
    if forma.kind == "label" and forma.simbolo:
        return [(f"{forma.simbolo} = {forma.testo}", forma.campo)]
    if forma.kind == "arrow" and forma.testo:
        return [(forma.testo, forma.campo)]
    if forma.kind == "diagram":
        return [(t, None) for t in (forma.etichette or ()) if t]
    return []


def _collegato_da_solo(testo: str, campi: dict[str, tuple[str, str, float | None]]) -> bool:
    match = TESTO_RE.match(testo)
    if not match:
        return False
    simbolo, mostrato, unita = match.group(1), match.group(2), _unita(match.group(3))
    valore = _numero(mostrato)
    decimali = len(mostrato.split(",")[1]) if "," in mostrato else 0
    return any(
        s == simbolo and u == unita and valore is not None and abs(valore - v) <= 0.5 * 10 ** -decimali + 1e-9
        for s, u, v in campi.values()
    )


def _sketch_esempio(tool: Tool):
    report = execute(tool, dict(tool.example))
    return getattr(report.data, "schizzo", None) if report.data is not None else None


@pytest.mark.unit
@pytest.mark.parametrize("name", sorted(n for n, t in discover().items() if t.example is not None and "schizzo" in t.output_model.model_fields))
def test_ogni_testo_con_il_simbolo_di_un_dato_e_collegato(name: str) -> None:
    tool = discover()[name]
    sketch = _sketch_esempio(tool)
    if sketch is None:
        pytest.skip("nessuno schizzo sull'esempio")
    campi = _campi_numerici(tool)
    simboli = {s for s, _, _ in campi.values() if s}
    problemi = []
    for vista in sketch.viste:
        for forma in vista.forme:
            for testo, campo in _testi(forma):
                if campo is not None and campo not in campi:
                    problemi.append(f"{vista.titolo}: {testo!r} ha campo={campo!r} che non è un dato numerico")
                    continue
                match = TESTO_RE.match(testo)
                if campo is None and match and match.group(1) in simboli and not _collegato_da_solo(testo, campi):
                    problemi.append(f"{vista.titolo}: {testo!r} porta il simbolo di un dato ma non è collegato: mettere campo=")
    assert problemi == [], "\n".join(problemi)

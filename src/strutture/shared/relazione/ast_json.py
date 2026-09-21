"""AST -> JSON-able dict, the wire format sent to the browser (docs/architecture-phase2.md §3).

`{"t":"num","v":0.4}` · `{"t":"id","base":"M","sub":"Rd,x"}` (`sub` always present, `""` when
there is none — one shape, no optional-key handling on the JS side) · `{"t":"op","op":"*",
"a":…,"b":…}` · `{"t":"neg","a":…}` · `{"t":"par","a":…}` (source parentheses are kept) ·
`{"t":"fn","name":"sqrt","args":[…]}` · `{"t":"cmp","op":"<=","a":…,"b":…}`.
"""
from typing import Any

from .notazione import Fn, Id, Neg, Nodo, Num, Op, Par


def ast_a_json(nodo: Nodo) -> dict[str, Any]:
    """Recursively convert a parsed AST into the plain-dict wire format of §3."""
    if isinstance(nodo, Num):
        return {"t": "num", "v": nodo.v}
    if isinstance(nodo, Id):
        return {"t": "id", "base": nodo.base, "sub": nodo.sub}
    if isinstance(nodo, Neg):
        return {"t": "neg", "a": ast_a_json(nodo.a)}
    if isinstance(nodo, Par):
        return {"t": "par", "a": ast_a_json(nodo.a)}
    if isinstance(nodo, Fn):
        return {"t": "fn", "name": nodo.name, "args": [ast_a_json(arg) for arg in nodo.args]}
    if isinstance(nodo, Op):
        return {"t": "op", "op": nodo.op, "a": ast_a_json(nodo.a), "b": ast_a_json(nodo.b)}
    return {"t": "cmp", "op": nodo.op, "a": ast_a_json(nodo.a), "b": ast_a_json(nodo.b)}

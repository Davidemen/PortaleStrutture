"""AST -> JSON-able dict, exactly the shapes of docs/architecture-phase2.md §3."""
import json

import pytest

from strutture.shared.relazione.ast_json import ast_a_json
from strutture.shared.relazione.notazione import analizza

pytestmark = pytest.mark.unit


def test_num_shape():
    assert ast_a_json(analizza("0.4")) == {"t": "num", "v": 0.4}


def test_id_shape_with_and_without_subscript():
    assert ast_a_json(analizza("M_Rd,x")) == {"t": "id", "base": "M", "sub": "Rd,x"}
    assert ast_a_json(analizza("d")) == {"t": "id", "base": "d", "sub": ""}


def test_op_shape():
    assert ast_a_json(analizza("a * b")) == {
        "t": "op", "op": "*", "a": {"t": "id", "base": "a", "sub": ""}, "b": {"t": "id", "base": "b", "sub": ""},
    }


def test_neg_and_par_shapes():
    assert ast_a_json(analizza("-x")) == {"t": "neg", "a": {"t": "id", "base": "x", "sub": ""}}
    assert ast_a_json(analizza("(x)")) == {"t": "par", "a": {"t": "id", "base": "x", "sub": ""}}


def test_fn_shape():
    assert ast_a_json(analizza("sqrt(x)")) == {"t": "fn", "name": "sqrt", "args": [{"t": "id", "base": "x", "sub": ""}]}


def test_cmp_shape():
    assert ast_a_json(analizza("a <= 1")) == {
        "t": "cmp", "op": "<=", "a": {"t": "id", "base": "a", "sub": ""}, "b": {"t": "num", "v": 1.0},
    }


def test_full_tree_is_json_serialisable():
    nodo = analizza("A_s * f_yd * (d - 0.4 * x)")
    serializzato = json.dumps(ast_a_json(nodo), ensure_ascii=False)
    assert json.loads(serializzato) == ast_a_json(nodo)

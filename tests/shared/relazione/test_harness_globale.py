"""The two global parametrised tests of docs/architecture-phase2.md §4: every tool that declares
`relazione` must produce a coherent trace on its own example, and every highlighted output must be
explained by some `Passo`. Each adopting package additionally runs `assert_relazione_coerente`
against its own golden-case inputs, in its own test file (§6: "relazione.py + tests through the
harness, nothing else") — golden cases are not registered anywhere generic enough for this
tool-agnostic module to enumerate them.
"""
import pytest

from strutture.shared.tool import Tool, discover
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit


def _tools_con_relazione() -> list[Tool]:
    return sorted((tool for tool in discover().values() if tool.relazione is not None), key=lambda t: t.name)


@pytest.mark.parametrize("tool", _tools_con_relazione(), ids=lambda tool: tool.name)
def test_ogni_tool_con_relazione_e_coerente_sul_proprio_esempio(tool: Tool) -> None:
    assert tool.example is not None, f"{tool.name}: dichiara relazione ma non ha un example"
    assert_relazione_coerente(tool, tool.example)


@pytest.mark.parametrize("tool", _tools_con_relazione(), ids=lambda tool: tool.name)
def test_ogni_highlight_e_spiegato_da_un_passo(tool: Tool) -> None:
    assert_ogni_highlight_e_spiegato(tool, tool.example)


def test_at_least_one_tool_declares_relazione() -> None:
    """Guards against the parametrised tests above silently collecting zero cases."""
    assert _tools_con_relazione(), "nessun tool dichiara relazione: la demo di adozione manca"

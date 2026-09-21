"""check.py: unknown tools, missing output paths, duplicate titles, empty clausola, orphan legacy() ids."""
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from strutture.shared.divergences.check import (
    CheckReport,
    duplicate_title_errors,
    empty_clausola_warnings,
    legacy_ids_in_code,
    orphan_id_report,
    run_checks,
    unknown_output_errors,
    unknown_tool_errors,
)
from strutture.shared.divergences.models import Divergence
from strutture.shared.report import success
from strutture.shared.tool import Tool

pytestmark = pytest.mark.unit


def _div(**overrides: object) -> Divergence:
    base = {
        "id": "demo/foo", "titolo": "Titolo di esempio", "tipo": "errore_foglio",
        "strumenti": ("demo-tool",), "foglio": "il foglio fa X", "corretto": "il codice fa Y",
    }
    return Divergence.model_validate({**base, **overrides})


# --- fixture tool with a nested group, an optional nested field and a rows tuple ---------------

class Geometria(BaseModel):
    model_config = ConfigDict(frozen=True)
    b_mm: float
    h_mm: float


class Riga(BaseModel):
    model_config = ConfigDict(frozen=True)
    mrd_kNm: float


class Output(BaseModel):
    model_config = ConfigDict(frozen=True)
    geometria: Geometria
    extra: Geometria | None = None
    righe: tuple[Riga, ...] = ()


class Input(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float = 1.0


DEMO_TOOL = Tool(
    "demo-tool", "Demo", "Test", "-", Input, Output,
    lambda inputs: success(Output(geometria=Geometria(b_mm=1, h_mm=1)), inputs),
)
TOOLS = {"demo-tool": DEMO_TOOL}


# --- unknown tool / output path -----------------------------------------------------------------

def test_unknown_tool_is_an_error() -> None:
    errors = unknown_tool_errors((_div(strumenti=("ghost-tool",)),), frozenset({"demo-tool"}))
    assert errors == ("demo/foo: unknown tool 'ghost-tool' (not in strutture.shared.tool.discover())",)


def test_known_tool_is_not_an_error() -> None:
    assert unknown_tool_errors((_div(),), frozenset({"demo-tool"})) == ()


def test_existing_nested_output_path_is_accepted() -> None:
    d = _div(uscite=("geometria.b_mm",))
    assert unknown_output_errors((d,), TOOLS) == ()


def test_missing_output_path_is_an_error() -> None:
    d = _div(uscite=("geometria.non_esiste",))
    assert unknown_output_errors((d,), TOOLS) == (
        "demo/foo: output path 'geometria.non_esiste' not found in the output schema of any of ['demo-tool']",
    )


def test_a_path_only_has_to_exist_in_one_of_the_entry_tools() -> None:
    """One divergence can affect several tools whose outputs are structured differently
    (sisma-completo nests what sisma-parametri-sito exposes at top level)."""
    from pydantic import BaseModel

    class Flat(BaseModel):
        ss: float = 1.0

    other = Tool("other-tool", "Altro", "Test", "-", Flat, Flat, lambda i: None)
    both = {**TOOLS, "other-tool": other}
    d = _div(strumenti=("demo-tool", "other-tool"), uscite=("geometria.b_mm", "ss"))
    assert unknown_output_errors((d,), both) == ()
    assert len(unknown_output_errors((_div(strumenti=("demo-tool", "other-tool"), uscite=("nowhere",)),), both)) == 1


def test_rows_tuple_column_path_is_accepted() -> None:
    d = _div(uscite=("righe.mrd_kNm",))
    assert unknown_output_errors((d,), TOOLS) == ()


def test_optional_nested_field_path_is_accepted() -> None:
    d = _div(uscite=("extra.h_mm",))
    assert unknown_output_errors((d,), TOOLS) == ()


def test_output_path_for_unknown_tool_is_skipped_not_crashed() -> None:
    d = _div(strumenti=("ghost-tool",), uscite=("whatever",))
    assert unknown_output_errors((d,), TOOLS) == ()


# --- duplicate titles --------------------------------------------------------------------------

def test_duplicate_title_within_unit_is_an_error() -> None:
    a = _div(id="demo/a", titolo="Stesso titolo")
    b = _div(id="demo/b", titolo="Stesso titolo")
    errors = duplicate_title_errors((a, b))
    assert len(errors) == 1
    assert "duplicate titolo" in errors[0]


def test_same_title_across_units_is_fine() -> None:
    a = _div(id="demo/a", titolo="Stesso titolo")
    b = _div(id="altro/b", titolo="Stesso titolo")
    assert duplicate_title_errors((a, b)) == ()


# --- empty clausola --------------------------------------------------------------------------

def test_empty_clausola_on_errore_foglio_is_a_warning_not_an_error() -> None:
    d = _div(tipo="errore_foglio", clausola="")
    assert empty_clausola_warnings((d,)) == ("demo/foo: tipo=errore_foglio but clausola is empty",)


def test_empty_clausola_on_scelta_ingegneristica_is_not_flagged() -> None:
    d = _div(tipo="scelta_ingegneristica", clausola="")
    assert empty_clausola_warnings((d,)) == ()


def test_filled_clausola_is_not_flagged() -> None:
    d = _div(tipo="aggiornamento_normativo", clausola="NTC2018 §4.1")
    assert empty_clausola_warnings((d,)) == ()


# --- ast-based legacy() collection --------------------------------------------------------------

def test_legacy_ids_are_collected_from_a_fixture_source_tree(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg" / "sub"
    pkg.mkdir(parents=True)
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "rule.py").write_text(
        "from strutture.shared.divergences import legacy\n"
        "def f(legacy_compat):\n"
        "    if legacy('demo/foo', legacy_compat):\n"
        "        pass\n"
        "    if marker.legacy('demo/bar', legacy_compat):\n"
        "        pass\n"
        "    legacy(some_variable, legacy_compat)\n"  # non-constant first arg: ignored
        "    legacy_lookalike('demo/not-a-call')\n"   # different function name: ignored
        "    legacy()\n",  # no args: ignored, must not crash
        encoding="utf-8",
    )
    assert legacy_ids_in_code(tmp_path) == frozenset({"demo/foo", "demo/bar"})


def test_orphan_report_splits_missing_from_unused() -> None:
    errors, warnings = orphan_id_report(frozenset({"demo/used", "demo/unused"}), frozenset({"demo/used", "demo/ghost"}))
    assert errors == ("legacy() id 'demo/ghost' used in code but missing from the register",)
    assert warnings == ("demo/unused: non ancora collegati nel codice (nessuna chiamata legacy())",)


# --- orchestrator + CLI exit code ----------------------------------------------------------------

def test_run_checks_aggregates_errors_and_warnings(tmp_path: Path) -> None:
    (tmp_path / "code.py").write_text("legacy('demo/foo', True)\n", encoding="utf-8")
    register = (_div(strumenti=("ghost-tool",), tipo="errore_foglio", clausola=""),)
    report = run_checks(register, TOOLS, tmp_path)
    assert any("ghost-tool" in e for e in report.errors)
    assert any("clausola is empty" in w for w in report.warnings)
    assert report.exit_code == 1


def test_report_exit_code_is_zero_without_errors() -> None:
    assert CheckReport(errors=(), warnings=("just a warning",)).exit_code == 0


def test_report_exit_code_is_one_with_errors() -> None:
    assert CheckReport(errors=("boom",)).exit_code == 1

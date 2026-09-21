"""render.py: deterministic markdown generation, tested against fixtures (never the real docs)."""
from pathlib import Path

import pytest

from strutture.shared.divergences.models import Divergence
from strutture.shared.divergences.render import render_all, render_unit, units_of, write_all

pytestmark = pytest.mark.unit


def _div(**overrides: object) -> Divergence:
    base = {
        "id": "demo/foo", "titolo": "Titolo di esempio", "tipo": "errore_foglio",
        "strumenti": ("demo-tool",), "foglio": "il foglio fa X", "corretto": "il codice fa Y",
        "clausola": "NTC2018 §4.1", "impatto": "nessuno",
    }
    return Divergence.model_validate({**base, **overrides})


def test_render_unit_of_empty_tuple_is_still_valid_markdown() -> None:
    text = render_unit(())
    assert text.startswith("<!-- GENERATED FILE")
    assert "do not edit by hand" in text.lower()


def test_render_unit_header_names_the_unit() -> None:
    text = render_unit((_div(id="ca-pilastri/x"),))
    assert "# Divergences — `ca-pilastri`" in text


def test_render_unit_groups_by_tipo_with_one_table_each() -> None:
    a = _div(id="demo/a", tipo="errore_foglio")
    b = _div(id="demo/b", tipo="scelta_ingegneristica")
    text = render_unit((a, b))
    assert "## Errori del foglio" in text
    assert "## Scelte ingegneristiche" in text
    assert text.index("## Errori del foglio") < text.index("## Scelte ingegneristiche")


def test_render_unit_skips_tipi_with_no_entries() -> None:
    text = render_unit((_div(tipo="errore_foglio"),))
    assert "## Aggiornamenti normativi" not in text
    assert "## Da verificare" not in text


def test_table_has_the_contract_columns_in_order() -> None:
    text = render_unit((_div(),))
    assert "| titolo | foglio | corretto | clausola | impatto | strumenti |" in text


def test_row_values_and_strumenti_join_appear_in_table() -> None:
    d = _div(strumenti=("tool-a", "tool-b"))
    text = render_unit((d,))
    assert "| Titolo di esempio | il foglio fa X | il codice fa Y | NTC2018 §4.1 | nessuno | tool-a, tool-b |" in text


def test_pipe_and_newline_in_free_text_are_escaped() -> None:
    d = _div(foglio="riga1\nriga2 | con pipe")
    text = render_unit((d,))
    assert "riga1 riga2 \\| con pipe" in text


def test_render_is_deterministic() -> None:
    divergences = (_div(id="demo/a"), _div(id="demo/b", tipo="scelta_ingegneristica"))
    assert render_unit(divergences) == render_unit(divergences)


def test_render_all_groups_by_unit() -> None:
    register = (_div(id="demo/a"), _div(id="altro/b", tipo="scelta_ingegneristica"))
    rendered = render_all(register)
    assert set(rendered) == {"demo", "altro"}
    assert "# Divergences — `demo`" in rendered["demo"]
    assert "# Divergences — `altro`" in rendered["altro"]


def test_units_of_is_sorted_and_deduplicated() -> None:
    register = (_div(id="demo/a"), _div(id="demo/b"), _div(id="altro/c"))
    assert units_of(register) == ("altro", "demo")


def test_write_all_writes_one_file_per_unit(tmp_path: Path) -> None:
    register = (_div(id="demo/a"), _div(id="altro/b"))
    docs_dir = tmp_path / "divergences"
    paths = write_all(register, docs_dir)
    assert {p.name for p in paths} == {"demo.md", "altro.md"}
    assert (docs_dir / "demo.md").read_text(encoding="utf-8") == render_unit((_div(id="demo/a"),))


def test_write_all_creates_missing_directory(tmp_path: Path) -> None:
    docs_dir = tmp_path / "nested" / "divergences"
    write_all((_div(),), docs_dir)
    assert docs_dir.is_dir()

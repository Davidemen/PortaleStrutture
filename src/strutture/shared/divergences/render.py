"""Render `docs/divergences/<unita>.md` from the JSON register.

`python -m strutture.shared.divergences.render` regenerates every unit's file from the packaged
register. `render_unit` is pure (no I/O) so it is tested directly; the CLI writes the files.
"""
from pathlib import Path

from .loader import load_register
from .models import Divergence, Tipo

DOCS_DIR = Path(__file__).resolve().parents[4] / "docs" / "divergences"

TIPO_ORDER: tuple[Tipo, ...] = ("errore_foglio", "aggiornamento_normativo", "scelta_ingegneristica", "da_verificare")
TIPO_TITLES: dict[Tipo, str] = {
    "errore_foglio": "Errori del foglio",
    "aggiornamento_normativo": "Aggiornamenti normativi",
    "scelta_ingegneristica": "Scelte ingegneristiche",
    "da_verificare": "Da verificare",
}
COLUMNS: tuple[str, ...] = ("titolo", "foglio", "corretto", "clausola", "impatto", "strumenti", "modalità Excel")
GENERATED_HEADER = (
    "<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, "
    "rendered by `python -m strutture.shared.divergences.render`. -->"
)


def render_unit(divergences: tuple[Divergence, ...]) -> str:
    """One markdown document for a single unit: one table per `tipo` present, in TIPO_ORDER."""
    unit = divergences[0].id.split("/", 1)[0] if divergences else "unita"
    lines = [GENERATED_HEADER, "", f"# Divergences — `{unit}`"]
    for tipo in TIPO_ORDER:
        rows = tuple(d for d in divergences if d.tipo == tipo)
        if rows:
            lines += ["", f"## {TIPO_TITLES[tipo]}", "", _table(rows)]
    return "\n".join(lines).rstrip("\n") + "\n"


def _table(rows: tuple[Divergence, ...]) -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    separator = "|" + "|".join("---" for _ in COLUMNS) + "|"
    body = "\n".join(_row(d) for d in rows)
    return f"{header}\n{separator}\n{body}"


def modalita_excel(d: Divergence) -> str:
    """How Excel mode (`legacy_compat`) relates to the entry — the one thing an engineer validating
    the tool against the spreadsheet must know: an entry that is NOT reproduced never shows up in a
    side-by-side comparison of the two modes."""
    if d.ramo == "codice":
        return "riprodotta"
    if d.ramo == "condiviso":
        insieme = f" insieme a {', '.join(d.riprodotta_da)}" if d.riprodotta_da else ""
        return f"riprodotta{insieme} — {d.motivo_senza_ramo}"
    return f"NON riprodotta — {d.motivo_senza_ramo}"


def _row(d: Divergence) -> str:
    values = (d.titolo, d.foglio, d.corretto, d.clausola, d.impatto, ", ".join(d.strumenti), modalita_excel(d))
    return "| " + " | ".join(_escape(v) for v in values) + " |"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def units_of(register: tuple[Divergence, ...]) -> tuple[str, ...]:
    return tuple(sorted({d.id.split("/", 1)[0] for d in register}))


def render_all(register: tuple[Divergence, ...]) -> dict[str, str]:
    """unit -> rendered markdown, for every unit present in the register."""
    return {unit: render_unit(tuple(d for d in register if d.id.split("/", 1)[0] == unit)) for unit in units_of(register)}


def write_all(register: tuple[Divergence, ...], docs_dir: Path) -> tuple[Path, ...]:
    """Write every unit's markdown file under `docs_dir`; returns the paths written."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for unit, content in render_all(register).items():
        path = docs_dir / f"{unit}.md"
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def main() -> None:
    written = write_all(load_register(), DOCS_DIR)
    print(f"wrote {len(written)} divergence docs to {DOCS_DIR}")


if __name__ == "__main__":
    main()

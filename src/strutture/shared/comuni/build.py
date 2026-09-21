"""Reproducible build: merge the three workbook Comuni CSV snapshots into `data/comuni.csv`
(architecture.md §3, conflict C3). Fails loudly on any unresolved merge conflict or validation
violation, printing a conflict report.

Run with: uv run python -m strutture.shared.comuni.build
"""
import csv
import sys
from pathlib import Path

from .constants import CSV_FIELDNAMES, DATA_CSV_PATH
from .merge import MergeResult, SourceRow, merge_rows
from .validate import validate_rows

REPO_ROOT: Path = Path(__file__).resolve().parents[4]
SISMA_CSV: Path = REPO_ROOT / "build" / "data" / "sisma" / "comuni.csv"
VENTO_CSV: Path = REPO_ROOT / "build" / "data" / "vento" / "comuni.csv"
NEVE_CSV: Path = REPO_ROOT / "build" / "data" / "neve" / "comuni.csv"

SOURCE_COLUMNS: tuple[str, ...] = ("Regione", "Provincia", "Codice Istat", "Comune", "Sismica", "Vento", "Neve")


class ComuniBuildError(RuntimeError):
    """Unresolved merge conflict or validation violation; the report is the exception message."""


def read_source(path: Path) -> tuple[SourceRow, ...]:
    """Load one workbook's Comuni CSV snapshot into SourceRow tuples."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [col for col in SOURCE_COLUMNS if col not in (reader.fieldnames or [])]
        if missing:
            raise ComuniBuildError(f"{path}: missing expected columns {missing}")
        return tuple(_row_from_csv(row) for row in reader)


def _row_from_csv(row: dict[str, str]) -> SourceRow:
    return SourceRow(
        regione=row["Regione"].strip(),
        provincia=row["Provincia"].strip(),
        istat=row["Codice Istat"].strip(),
        comune=row["Comune"].strip(),
        sismica=row["Sismica"].strip(),
        vento=row["Vento"].strip(),
        neve=row["Neve"].strip(),
    )


def build(
    sisma_csv: Path = SISMA_CSV,
    vento_csv: Path = VENTO_CSV,
    neve_csv: Path = NEVE_CSV,
    output_csv: Path = DATA_CSV_PATH,
) -> int:
    """Merge, validate, and write the Comuni database. Returns the row count written.

    Raises ComuniBuildError (with a full report) on any unresolved conflict or violation.
    """
    result = merge_rows(read_source(sisma_csv), read_source(vento_csv), read_source(neve_csv))
    if result.conflicts:
        raise ComuniBuildError(_report("unresolved merge conflicts", result.conflicts))
    violations = validate_rows(result.rows)
    if violations:
        raise ComuniBuildError(_report("validation violations", violations))
    _write(output_csv, result)
    return len(result.rows)


def _report(title: str, lines: tuple[str, ...]) -> str:
    body = "\n".join(f"  - {line}" for line in lines)
    return f"comuni build failed: {len(lines)} {title}\n{body}"


def _write(output_csv: Path, result: MergeResult) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(result.rows)


def main() -> None:
    try:
        count = build()
    except ComuniBuildError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    print(f"wrote {count} comuni to {DATA_CSV_PATH}")


if __name__ == "__main__":
    main()

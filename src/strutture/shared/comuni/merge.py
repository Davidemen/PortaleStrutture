"""Pure per-column provenance merge of the three Comuni CSV snapshots (architecture.md §3, C3).

Regione / Istat / Comune / Sismica / Vento come from the sisma-vento snapshot (byte-identical to
each other in the source data). Provincia and the Neve zone come from the newer neve snapshot
(it has updated province names, e.g. "Monza e Brianza", and no blank Neve zones). Anything the
sisma and vento snapshots disagree on, or any comune missing from one of the three sources, is an
unresolved conflict the caller must fail on.
"""
from dataclasses import dataclass

SHARED_COLUMNS: tuple[str, ...] = ("regione", "comune", "sismica", "vento")


@dataclass(frozen=True)
class SourceRow:
    regione: str
    provincia: str
    istat: str
    comune: str
    sismica: str
    vento: str
    neve: str


@dataclass(frozen=True)
class MergeResult:
    rows: tuple[dict[str, str], ...]
    conflicts: tuple[str, ...]


def merge_rows(sisma: tuple[SourceRow, ...], vento: tuple[SourceRow, ...], neve: tuple[SourceRow, ...]) -> MergeResult:
    """Join the three snapshots on Codice Istat and apply the per-column provenance rule."""
    by_istat_vento = {row.istat: row for row in vento}
    by_istat_neve = {row.istat: row for row in neve}
    rows: list[dict[str, str]] = []
    conflicts: list[str] = []
    for base in sisma:
        v, n = by_istat_vento.get(base.istat), by_istat_neve.get(base.istat)
        if v is None or n is None:
            missing = "vento" if v is None else "neve"
            conflicts.append(f"istat {base.istat!r} ({base.comune!r}) missing from {missing} source")
            continue
        row_conflicts = _shared_column_conflicts(base, v)
        if row_conflicts:
            conflicts += row_conflicts
            continue
        rows.append({
            "regione": base.regione, "provincia": n.provincia, "istat": base.istat, "comune": base.comune,
            "zona_sismica": base.sismica, "zona_vento": base.vento, "zona_neve": n.neve,
        })
    return MergeResult(rows=tuple(rows), conflicts=tuple(conflicts))


def _shared_column_conflicts(base: SourceRow, other: SourceRow) -> list[str]:
    """Sisma and vento are expected byte-identical on SHARED_COLUMNS; flag any drift as unresolved."""
    return [
        f"istat {base.istat!r}: {col} differs sisma={getattr(base, col)!r} vento={getattr(other, col)!r}"
        for col in SHARED_COLUMNS
        if getattr(base, col) != getattr(other, col)
    ]

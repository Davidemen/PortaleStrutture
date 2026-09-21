"""Validation of the merged Comuni rows before they are written/loaded (architecture.md §3, C3):
"Validate on load: zonaVento ∈ 1..9, zonaSismica ∈ 1..4, zonaNeve ∈ enum, no blanks, unique Istat.
Fail the build on violation." Returns every violation found (not just the first) for one report.
"""
from collections import Counter

from .constants import VALID_ZONA_NEVE, VALID_ZONA_SISMICA, VALID_ZONA_VENTO

REQUIRED_FIELDS: tuple[str, ...] = (
    "regione", "provincia", "istat", "comune", "zona_sismica", "zona_vento", "zona_neve",
)


def validate_rows(rows: tuple[dict[str, str], ...]) -> tuple[str, ...]:
    violations: list[str] = []
    for index, row in enumerate(rows):
        violations += _blank_violations(index, row)
        violations += _zone_violations(index, row)
    violations += _duplicate_istat_violations(rows)
    return tuple(violations)


def _blank_violations(index: int, row: dict[str, str]) -> list[str]:
    return [
        f"row {index}: blank {field!r} (istat={row.get('istat')!r})"
        for field in REQUIRED_FIELDS
        if not row.get(field, "").strip()
    ]


def _zone_violations(index: int, row: dict[str, str]) -> list[str]:
    checks = (
        ("zona_sismica", VALID_ZONA_SISMICA),
        ("zona_vento", VALID_ZONA_VENTO),
        ("zona_neve", VALID_ZONA_NEVE),
    )
    return [
        f"row {index}: {field}={row.get(field)!r} not in {sorted(domain)} (istat={row.get('istat')!r})"
        for field, domain in checks
        if row.get(field) not in domain
    ]


def _duplicate_istat_violations(rows: tuple[dict[str, str], ...]) -> list[str]:
    counts = Counter(row.get("istat", "") for row in rows)
    return [f"duplicate istat {istat!r} ({n} rows)" for istat, n in counts.items() if n > 1]

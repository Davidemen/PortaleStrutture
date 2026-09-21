"""Ordered, idempotent schema migrations tracked in a `schema_version` table.

Add new migrations by appending to `MIGRATIONS`. Never edit an already-shipped entry — migration 1 stays exactly
as written so it keeps replaying identically on every existing database; later phases (projects, elements) append
migration 2, 3, ... instead of touching this one.
"""
from __future__ import annotations

import sqlite3

MIGRATION_1 = """
CREATE TABLE IF NOT EXISTS signoff (
    divergence_id TEXT PRIMARY KEY,
    stato TEXT NOT NULL,
    sigla TEXT NOT NULL DEFAULT '',
    nota TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS signoff_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    divergence_id TEXT NOT NULL,
    stato TEXT NOT NULL,
    sigla TEXT NOT NULL DEFAULT '',
    nota TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_signoff_history_divergence ON signoff_history (divergence_id, id);
"""

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, MIGRATION_1),
)


def _current_version(connection: sqlite3.Connection) -> int:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    row = connection.execute("SELECT MAX(version) AS version FROM schema_version").fetchone()
    return row["version"] or 0


def migrate(connection: sqlite3.Connection) -> None:
    """Apply every migration newer than the database's current version, in order, exactly once each."""
    current = _current_version(connection)
    for version, script in MIGRATIONS:
        if version <= current:
            continue
        connection.executescript(script)
        connection.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
            (version,),
        )
        connection.commit()

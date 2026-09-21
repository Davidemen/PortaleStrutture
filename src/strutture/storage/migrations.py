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

MIGRATION_2 = """
CREATE TABLE IF NOT EXISTS progetto (
    id TEXT PRIMARY KEY,
    codice TEXT NOT NULL DEFAULT '',
    nome TEXT NOT NULL,
    committente TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    revisione INTEGER NOT NULL DEFAULT 0,
    creato TEXT NOT NULL DEFAULT '',
    aggiornato TEXT NOT NULL DEFAULT '',
    eliminato TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_progetto_aggiornato ON progetto (aggiornato);

CREATE TABLE IF NOT EXISTS elemento (
    id TEXT PRIMARY KEY,
    progetto_id TEXT NOT NULL,
    strumento TEXT NOT NULL,
    nome TEXT NOT NULL,
    inputs TEXT NOT NULL DEFAULT '{}',
    sintesi TEXT NOT NULL DEFAULT '{}',
    stato TEXT NOT NULL DEFAULT 'non_verificato',
    modalita TEXT NOT NULL DEFAULT 'standard',
    versione_app TEXT NOT NULL DEFAULT '',
    provenienza TEXT NOT NULL DEFAULT '{}',
    revisione INTEGER NOT NULL DEFAULT 0,
    creato TEXT NOT NULL DEFAULT '',
    aggiornato TEXT NOT NULL DEFAULT '',
    eliminato TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_elemento_progetto ON elemento (progetto_id);
CREATE INDEX IF NOT EXISTS idx_elemento_aggiornato ON elemento (aggiornato);

CREATE TABLE IF NOT EXISTS elemento_revisione (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    elemento_id TEXT NOT NULL,
    revisione INTEGER NOT NULL,
    inputs TEXT NOT NULL DEFAULT '{}',
    sintesi TEXT NOT NULL DEFAULT '{}',
    sigla TEXT NOT NULL DEFAULT '',
    nota TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_elemento_revisione_elemento ON elemento_revisione (elemento_id, revisione);
"""

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, MIGRATION_1),
    (2, MIGRATION_2),
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

"""migrations.py: ordered, idempotent, forward-only schema migrations."""
from __future__ import annotations

import pytest

from strutture.storage.database import connect
from strutture.storage.migrations import MIGRATIONS, migrate


@pytest.mark.unit
def test_migrate_creates_tables(tmp_path):
    connection = connect(tmp_path / "db.sqlite")
    try:
        migrate(connection)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"signoff", "signoff_history", "schema_version"} <= tables
    finally:
        connection.close()


@pytest.mark.unit
def test_migrate_is_idempotent(tmp_path):
    connection = connect(tmp_path / "db.sqlite")
    try:
        migrate(connection)
        migrate(connection)  # second call must not raise or duplicate schema_version rows
        rows = connection.execute("SELECT version FROM schema_version").fetchall()
        assert sorted(row[0] for row in rows) == [version for version, _ in MIGRATIONS]
    finally:
        connection.close()


@pytest.mark.unit
def test_migrations_are_forward_only():
    versions = [version for version, _ in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert versions[0] == 1


@pytest.mark.unit
def test_migrate_survives_reopen(tmp_path):
    db_path = tmp_path / "reopen.db"
    first = connect(db_path)
    try:
        migrate(first)
    finally:
        first.close()

    second = connect(db_path)
    try:
        migrate(second)  # idempotent across process/connection boundaries too
        version = second.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert version == MIGRATIONS[-1][0]
    finally:
        second.close()

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
def test_migrate_creates_migration_2_tables(tmp_path):
    connection = connect(tmp_path / "db.sqlite")
    try:
        migrate(connection)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"progetto", "elemento", "elemento_revisione"} <= tables
        indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        assert {"idx_elemento_progetto", "idx_elemento_revisione_elemento"} <= indexes
    finally:
        connection.close()


@pytest.mark.unit
def test_migrate_from_version_1_preserves_signoff_data(tmp_path):
    from strutture.storage.signoff_sqlite import open_signoff_repository

    db_path = tmp_path
    repo = open_signoff_repository(db_path)  # runs migration 1 only, at the time it shipped
    repo.set("muro/d1", "approvato", "AB", nota="prima del passaggio a v2")

    connection = connect(db_path / "strutture.db")
    try:
        migrate(connection)  # now also applies migration 2
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"progetto", "elemento", "elemento_revisione", "signoff"} <= tables
        row = connection.execute("SELECT * FROM signoff WHERE divergence_id = ?", ("muro/d1",)).fetchone()
        assert row["sigla"] == "AB"
        assert row["nota"] == "prima del passaggio a v2"
    finally:
        connection.close()


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


@pytest.mark.unit
def test_migrate_creates_migration_3_tables(tmp_path):
    connection = connect(tmp_path / "db.sqlite")
    try:
        migrate(connection)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"impostazioni", "impostazioni_storia"} <= tables
    finally:
        connection.close()


@pytest.mark.unit
def test_migrate_from_version_2_preserves_existing_data(tmp_path):
    from strutture.storage.models import Progetto
    from strutture.storage.progetti_sqlite import open_project_repository

    db_path = tmp_path
    repo = open_project_repository(db_path)  # runs migrations 1-2 only, at the time it shipped
    created = repo.crea_progetto(Progetto(nome="Prova migrazione 3"))

    connection = connect(db_path / "strutture.db")
    try:
        migrate(connection)  # now also applies migration 3
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"impostazioni", "impostazioni_storia", "progetto", "elemento"} <= tables
        row = connection.execute("SELECT * FROM progetto WHERE id = ?", (created.id,)).fetchone()
        assert row["nome"] == "Prova migrazione 3"
        assert connection.execute("SELECT COUNT(*) FROM impostazioni").fetchone()[0] == 0
    finally:
        connection.close()

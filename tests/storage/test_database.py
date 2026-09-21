"""database.py: data-directory resolution and connection tuning."""
from __future__ import annotations

import sqlite3

import pytest

from strutture.storage import database


@pytest.mark.unit
def test_default_data_dir_is_project_root_var(tmp_path, monkeypatch):
    monkeypatch.delenv("STRUTTURE_DATA_DIR", raising=False)
    monkeypatch.setattr(database, "PROJECT_ROOT", tmp_path)
    data_dir = database.data_dir_from_env(env={})
    assert data_dir == tmp_path / "var"
    assert data_dir.is_dir()


@pytest.mark.unit
def test_env_override(tmp_path):
    custom = tmp_path / "custom-data"
    data_dir = database.data_dir_from_env(env={"STRUTTURE_DATA_DIR": str(custom)})
    assert data_dir == custom
    assert data_dir.is_dir()


@pytest.mark.unit
def test_default_data_dir_never_inside_src(monkeypatch):
    monkeypatch.delenv("STRUTTURE_DATA_DIR", raising=False)
    data_dir = database.data_dir_from_env(env={})
    src_root = database.PROJECT_ROOT / "src"
    assert src_root not in data_dir.parents
    assert data_dir == database.PROJECT_ROOT / "var"


@pytest.mark.unit
def test_connect_sets_pragmas(tmp_path):
    connection = database.connect(tmp_path / "test.db")
    try:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.row_factory is sqlite3.Row
    finally:
        connection.close()


@pytest.mark.unit
def test_session_commits_and_closes(tmp_path):
    db_path = tmp_path / "sub" / "test.db"
    with database.session(db_path) as connection:
        connection.execute("CREATE TABLE t (x INTEGER)")
        connection.execute("INSERT INTO t VALUES (1)")

    verify = sqlite3.connect(db_path)
    try:
        assert verify.execute("SELECT x FROM t").fetchone()[0] == 1
    finally:
        verify.close()


@pytest.mark.unit
def test_session_closes_on_error(tmp_path):
    db_path = tmp_path / "test.db"
    with pytest.raises(ValueError), database.session(db_path) as connection:
        connection.execute("CREATE TABLE t (x INTEGER)")
        raise ValueError("boom")
    # a fresh connection must be able to open the file without a stale lock
    verify = sqlite3.connect(db_path)
    verify.close()

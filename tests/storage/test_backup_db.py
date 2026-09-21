"""scripts/backup_db.py: online backup, retention, and CLI wiring."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "backup_db.py"


def _load_backup_module():
    spec = importlib.util.spec_from_file_location("strutture_backup_db_script", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def backup_db(request):
    module = _load_backup_module()
    request.addfinalizer(lambda: sys.modules.pop("strutture_backup_db_script", None))
    return module


def _make_database(data_dir: Path) -> None:
    from strutture.storage.signoff_sqlite import open_signoff_repository

    repo = open_signoff_repository(data_dir)
    repo.set("muro/d1", "approvato", "AB")


def _fixed_now(offset_seconds: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset_seconds)


@pytest.mark.unit
def test_backup_produces_readable_copy(tmp_path, backup_db):
    _make_database(tmp_path)
    backup_path = backup_db.backup_database(tmp_path, keep=30)
    assert backup_path.exists()

    connection = sqlite3.connect(backup_path)
    try:
        row = connection.execute("SELECT sigla FROM signoff WHERE divergence_id = ?", ("muro/d1",)).fetchone()
        assert row[0] == "AB"
    finally:
        connection.close()


@pytest.mark.unit
def test_backup_missing_database_raises(tmp_path, backup_db):
    with pytest.raises(FileNotFoundError):
        backup_db.backup_database(tmp_path, keep=30)


@pytest.mark.unit
def test_backup_keeps_newest_n(tmp_path, backup_db):
    _make_database(tmp_path)
    for i in range(5):
        backup_db.backup_database(tmp_path, keep=3, now=_fixed_now(i))

    backups = sorted((tmp_path / "backups").glob("strutture-*.db"))
    assert len(backups) == 3
    assert backups[-1].name == f"strutture-{_fixed_now(4).strftime(backup_db.TIMESTAMP_FORMAT)}.db"


@pytest.mark.unit
def test_main_prints_backup_path(tmp_path, backup_db, capsys):
    _make_database(tmp_path)
    backup_db.main(["--data-dir", str(tmp_path), "--keep", "5"])
    out = capsys.readouterr().out.strip()
    assert Path(out).exists()
    assert Path(out).parent == tmp_path / "backups"

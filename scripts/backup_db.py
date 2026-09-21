"""Back up the SQLite database with sqlite3's online backup API, keeping the newest N copies.

Usage: uv run python scripts/backup_db.py [--data-dir PATH] [--keep N]
Works unchanged on Windows and macOS (pathlib only, no shell syntax).
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from strutture.storage.database import data_dir_from_env

DEFAULT_KEEP = 30
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
DB_FILENAME = "strutture.db"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Back up the strutture SQLite database.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Defaults to STRUTTURE_DATA_DIR or var/")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help=f"Backups to retain (default {DEFAULT_KEEP})")
    return parser.parse_args(argv)


def backup_database(data_dir: Path, keep: int, now: datetime | None = None) -> Path:
    """Write a timestamped copy of `<data_dir>/strutture.db` under `<data_dir>/backups`, prune, return its path."""
    source_path = data_dir / DB_FILENAME
    if not source_path.exists():
        raise FileNotFoundError(f"no database at {source_path}")
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(UTC)).strftime(TIMESTAMP_FORMAT)
    target_path = backups_dir / f"strutture-{timestamp}.db"

    source = sqlite3.connect(source_path)
    try:
        target = sqlite3.connect(target_path)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()

    _prune_old_backups(backups_dir, keep)
    return target_path


def _prune_old_backups(backups_dir: Path, keep: int) -> None:
    backups = sorted(backups_dir.glob("strutture-*.db"))
    stale = backups[:-keep] if keep > 0 else backups
    for backup in stale:
        backup.unlink()


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    data_dir = args.data_dir if args.data_dir is not None else data_dir_from_env()
    backup_path = backup_database(data_dir, args.keep)
    print(backup_path)


if __name__ == "__main__":
    main()

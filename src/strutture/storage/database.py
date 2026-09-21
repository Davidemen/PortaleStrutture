"""SQLite connection helpers: data-directory resolution and short-lived, per-operation connections."""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR_NAME = "var"
BUSY_TIMEOUT_MS = 5_000


def data_dir_from_env(env: Mapping[str, str] | None = None) -> Path:
    """Resolve the data directory from STRUTTURE_DATA_DIR, defaulting to `<project root>/var`.

    Created on demand; never inside `src/`.
    """
    source = os.environ if env is None else env
    raw = source.get("STRUTTURE_DATA_DIR", "").strip()
    data_dir = Path(raw).expanduser() if raw else PROJECT_ROOT / DEFAULT_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def connect(path: Path) -> sqlite3.Connection:
    """Open a connection tuned for a multi-threaded app: WAL, foreign keys, busy timeout, row access by name."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    return connection


@contextmanager
def session(path: Path) -> Iterator[sqlite3.Connection]:
    """One short-lived connection per operation: commit on success, always close.

    The app runs handlers in a threadpool; opening a fresh connection per call (rather than sharing one across
    threads) is what makes the repository thread-safe.
    """
    connection = connect(path)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

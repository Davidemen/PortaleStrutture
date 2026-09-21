"""SQLite-backed SignoffRepository: a short-lived connection per operation keeps it thread-safe."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .database import session
from .interfaces import SignoffRepository
from .migrations import migrate
from .models import Signoff, Stato

DB_FILENAME = "strutture.db"


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_signoff(row: sqlite3.Row) -> Signoff:
    return Signoff(
        divergence_id=row["divergence_id"],
        stato=row["stato"],
        sigla=row["sigla"],
        nota=row["nota"],
        data=row["data"],
    )


class SqliteSignoffRepository:
    """Implements `SignoffRepository` against a SQLite file at `db_path`."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def get(self, divergence_id: str) -> Signoff:
        with session(self._db_path) as connection:
            row = connection.execute(
                "SELECT * FROM signoff WHERE divergence_id = ?", (divergence_id,)
            ).fetchone()
        if row is None:
            return Signoff(divergence_id=divergence_id)
        return _row_to_signoff(row)

    def list_all(self) -> dict[str, Signoff]:
        with session(self._db_path) as connection:
            rows = connection.execute("SELECT * FROM signoff").fetchall()
        return {row["divergence_id"]: _row_to_signoff(row) for row in rows}

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        record = Signoff(divergence_id=divergence_id, stato=stato, sigla=sigla, nota=nota, data=_utc_now_iso())
        payload = record.model_dump()
        with session(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO signoff (divergence_id, stato, sigla, nota, data)
                VALUES (:divergence_id, :stato, :sigla, :nota, :data)
                ON CONFLICT(divergence_id) DO UPDATE SET
                    stato = excluded.stato, sigla = excluded.sigla, nota = excluded.nota, data = excluded.data
                """,
                payload,
            )
            connection.execute(
                """
                INSERT INTO signoff_history (divergence_id, stato, sigla, nota, data)
                VALUES (:divergence_id, :stato, :sigla, :nota, :data)
                """,
                payload,
            )
        return record

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        with session(self._db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM signoff_history WHERE divergence_id = ? ORDER BY id ASC",
                (divergence_id,),
            ).fetchall()
        return tuple(_row_to_signoff(row) for row in rows)


def open_signoff_repository(data_dir: Path) -> SignoffRepository:
    """Run migrations against `<data_dir>/strutture.db` and return a ready repository."""
    db_path = data_dir / DB_FILENAME
    with session(db_path) as connection:
        migrate(connection)
    return SqliteSignoffRepository(db_path)

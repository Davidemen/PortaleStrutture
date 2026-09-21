"""SQLite-backed ProjectRepository: a short-lived connection per operation, one transaction per write."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .database import session, write_session
from .interfaces import ConflictError, NotFoundError, ProjectRepository
from .migrations import migrate
from .models import Elemento, Progetto, RevisioneElemento

DB_FILENAME = "strutture.db"


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id() -> str:
    return uuid.uuid4().hex


def _dumps(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False)


def _row_to_progetto(row: sqlite3.Row) -> Progetto:
    return Progetto(
        id=row["id"],
        codice=row["codice"],
        nome=row["nome"],
        committente=row["committente"],
        note=row["note"],
        revisione=row["revisione"],
        creato=row["creato"],
        aggiornato=row["aggiornato"],
        eliminato=row["eliminato"],
    )


def _row_to_elemento(row: sqlite3.Row) -> Elemento:
    return Elemento(
        id=row["id"],
        progetto_id=row["progetto_id"],
        strumento=row["strumento"],
        nome=row["nome"],
        inputs=json.loads(row["inputs"]),
        sintesi=json.loads(row["sintesi"]),
        stato=row["stato"],
        modalita=row["modalita"],
        versione_app=row["versione_app"],
        provenienza=json.loads(row["provenienza"]),
        revisione=row["revisione"],
        creato=row["creato"],
        aggiornato=row["aggiornato"],
        eliminato=row["eliminato"],
    )


def _row_to_revisione(row: sqlite3.Row) -> RevisioneElemento:
    return RevisioneElemento(
        elemento_id=row["elemento_id"],
        revisione=row["revisione"],
        inputs=json.loads(row["inputs"]),
        sintesi=json.loads(row["sintesi"]),
        sigla=row["sigla"],
        nota=row["nota"],
        data=row["data"],
    )


class SqliteProjectRepository:
    """Implements `ProjectRepository` against a SQLite file at `db_path`."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    # ---- progetti ----

    def list_progetti(self, *, inclusi_eliminati: bool = False) -> tuple[Progetto, ...]:
        query = "SELECT * FROM progetto"
        if not inclusi_eliminati:
            query += " WHERE eliminato = ''"
        query += " ORDER BY aggiornato DESC, id ASC"
        with session(self._db_path) as connection:
            rows = connection.execute(query).fetchall()
        return tuple(_row_to_progetto(row) for row in rows)

    def get_progetto(self, progetto_id: str) -> Progetto:
        with session(self._db_path) as connection:
            row = connection.execute("SELECT * FROM progetto WHERE id = ?", (progetto_id,)).fetchone()
        if row is None:
            raise NotFoundError(progetto_id)
        return _row_to_progetto(row)

    def crea_progetto(self, progetto: Progetto) -> Progetto:
        now = _utc_now_iso()
        record = progetto.model_copy(update={"id": _new_id(), "revisione": 1, "creato": now, "aggiornato": now,
                                              "eliminato": ""})
        with session(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO progetto (id, codice, nome, committente, note, revisione, creato, aggiornato, eliminato)
                VALUES (:id, :codice, :nome, :committente, :note, :revisione, :creato, :aggiornato, :eliminato)
                """,
                record.model_dump(),
            )
        return record

    def aggiorna_progetto(self, progetto: Progetto) -> Progetto:
        with write_session(self._db_path) as connection:
            current = _fetch_progetto_for_write(connection, progetto.id)
            _check_revisione(current.revisione, progetto.revisione)
            now = _utc_now_iso()
            record = progetto.model_copy(update={"revisione": current.revisione + 1, "creato": current.creato,
                                                  "aggiornato": now, "eliminato": current.eliminato})
            connection.execute(
                """
                UPDATE progetto SET codice = :codice, nome = :nome, committente = :committente, note = :note,
                    revisione = :revisione, aggiornato = :aggiornato WHERE id = :id
                """,
                record.model_dump(),
            )
        return record

    def elimina_progetto(self, progetto_id: str, revisione: int) -> None:
        with write_session(self._db_path) as connection:
            current = _fetch_progetto_for_write(connection, progetto_id)
            _check_revisione(current.revisione, revisione)
            now = _utc_now_iso()
            connection.execute(
                "UPDATE progetto SET eliminato = ?, aggiornato = ?, revisione = ? WHERE id = ?",
                (now, now, current.revisione + 1, progetto_id),
            )

    def ripristina_progetto(self, progetto_id: str) -> Progetto:
        with write_session(self._db_path) as connection:
            row = connection.execute("SELECT * FROM progetto WHERE id = ?", (progetto_id,)).fetchone()
            if row is None:
                raise NotFoundError(progetto_id)
            current = _row_to_progetto(row)
            now = _utc_now_iso()
            new_revisione = current.revisione + 1
            connection.execute(
                "UPDATE progetto SET eliminato = '', aggiornato = ?, revisione = ? WHERE id = ?",
                (now, new_revisione, progetto_id),
            )
        return current.model_copy(update={"eliminato": "", "aggiornato": now, "revisione": new_revisione})

    # ---- elementi ----

    def list_elementi(self, progetto_id: str) -> tuple[Elemento, ...]:
        with session(self._db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM elemento WHERE progetto_id = ? AND eliminato = '' ORDER BY aggiornato DESC, id ASC",
                (progetto_id,),
            ).fetchall()
        return tuple(_row_to_elemento(row) for row in rows)

    def get_elemento(self, elemento_id: str) -> Elemento:
        with session(self._db_path) as connection:
            row = connection.execute("SELECT * FROM elemento WHERE id = ?", (elemento_id,)).fetchone()
        if row is None:
            raise NotFoundError(elemento_id)
        return _row_to_elemento(row)

    def crea_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        now = _utc_now_iso()
        record = elemento.model_copy(update={"id": _new_id(), "revisione": 1, "creato": now, "aggiornato": now,
                                              "eliminato": ""})
        with session(self._db_path) as connection:
            connection.execute(_INSERT_ELEMENTO, _elemento_payload(record))
            connection.execute(_INSERT_REVISIONE, _revisione_payload(record, sigla, nota, now))
        return record

    def aggiorna_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        with write_session(self._db_path) as connection:
            current = _fetch_elemento_for_write(connection, elemento.id)
            _check_revisione(current.revisione, elemento.revisione)
            now = _utc_now_iso()
            record = elemento.model_copy(update={"revisione": current.revisione + 1, "creato": current.creato,
                                                  "aggiornato": now, "eliminato": current.eliminato})
            connection.execute(_UPDATE_ELEMENTO, _elemento_payload(record))
            connection.execute(_INSERT_REVISIONE, _revisione_payload(record, sigla, nota, now))
        return record

    def duplica_elemento(self, elemento_id: str, nuovo_nome: str) -> Elemento:
        with write_session(self._db_path) as connection:
            row = connection.execute("SELECT * FROM elemento WHERE id = ?", (elemento_id,)).fetchone()
            if row is None or row["eliminato"] != "":
                raise NotFoundError(elemento_id)
            source = _row_to_elemento(row)
            now = _utc_now_iso()
            record = source.model_copy(update={"id": _new_id(), "nome": nuovo_nome, "revisione": 1, "creato": now,
                                                "aggiornato": now, "eliminato": ""})
            connection.execute(_INSERT_ELEMENTO, _elemento_payload(record))
            connection.execute(_INSERT_REVISIONE, _revisione_payload(record, "", "", now))
        return record

    def elimina_elemento(self, elemento_id: str, revisione: int) -> None:
        with write_session(self._db_path) as connection:
            current = _fetch_elemento_for_write(connection, elemento_id)
            _check_revisione(current.revisione, revisione)
            now = _utc_now_iso()
            connection.execute(
                "UPDATE elemento SET eliminato = ?, aggiornato = ?, revisione = ? WHERE id = ?",
                (now, now, current.revisione + 1, elemento_id),
            )

    def revisioni(self, elemento_id: str) -> tuple[RevisioneElemento, ...]:
        with session(self._db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM elemento_revisione WHERE elemento_id = ? ORDER BY revisione ASC",
                (elemento_id,),
            ).fetchall()
        return tuple(_row_to_revisione(row) for row in rows)


_INSERT_ELEMENTO = """
INSERT INTO elemento (id, progetto_id, strumento, nome, inputs, sintesi, stato, modalita, versione_app,
    provenienza, revisione, creato, aggiornato, eliminato)
VALUES (:id, :progetto_id, :strumento, :nome, :inputs, :sintesi, :stato, :modalita, :versione_app,
    :provenienza, :revisione, :creato, :aggiornato, :eliminato)
"""

_UPDATE_ELEMENTO = """
UPDATE elemento SET strumento = :strumento, nome = :nome, inputs = :inputs, sintesi = :sintesi, stato = :stato,
    modalita = :modalita, versione_app = :versione_app, provenienza = :provenienza, revisione = :revisione,
    aggiornato = :aggiornato WHERE id = :id
"""

_INSERT_REVISIONE = """
INSERT INTO elemento_revisione (elemento_id, revisione, inputs, sintesi, sigla, nota, data)
VALUES (:elemento_id, :revisione, :inputs, :sintesi, :sigla, :nota, :data)
"""


def _elemento_payload(elemento: Elemento) -> dict:
    payload = elemento.model_dump()
    payload["inputs"] = _dumps(elemento.inputs)
    payload["sintesi"] = _dumps(elemento.sintesi)
    payload["provenienza"] = _dumps(elemento.provenienza)
    return payload


def _revisione_payload(elemento: Elemento, sigla: str, nota: str, now: str) -> dict:
    return {
        "elemento_id": elemento.id,
        "revisione": elemento.revisione,
        "inputs": _dumps(elemento.inputs),
        "sintesi": _dumps(elemento.sintesi),
        "sigla": sigla,
        "nota": nota,
        "data": now,
    }


def _fetch_progetto_for_write(connection: sqlite3.Connection, progetto_id: str) -> Progetto:
    row = connection.execute("SELECT * FROM progetto WHERE id = ?", (progetto_id,)).fetchone()
    if row is None or row["eliminato"] != "":
        raise NotFoundError(progetto_id)
    return _row_to_progetto(row)


def _fetch_elemento_for_write(connection: sqlite3.Connection, elemento_id: str) -> Elemento:
    row = connection.execute("SELECT * FROM elemento WHERE id = ?", (elemento_id,)).fetchone()
    if row is None or row["eliminato"] != "":
        raise NotFoundError(elemento_id)
    return _row_to_elemento(row)


def _check_revisione(current: int, expected: int) -> None:
    if current != expected:
        raise ConflictError(f"revisione attesa {expected}, trovata {current}")


def open_project_repository(data_dir: Path) -> ProjectRepository:
    """Run migrations against `<data_dir>/strutture.db` and return a ready repository."""
    db_path = data_dir / DB_FILENAME
    with session(db_path) as connection:
        migrate(connection)
    return SqliteProjectRepository(db_path)

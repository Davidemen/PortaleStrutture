"""SQLite-backed ImpostazioniRepository: one row in `impostazioni`, append-only `impostazioni_storia`."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from strutture.shared.impostazioni.modelli import FABBRICA, Impostazioni, ImpostazioniSalvate

from .database import session, write_session
from .interfaces import ConflictError
from .migrations import migrate

logger = logging.getLogger(__name__)
DB_FILENAME = "strutture.db"
_AVVISO_CORROTTO = "Impostazioni salvate non leggibili in parte: usati i valori di fabbrica per {campi}."


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_salvate(row: sqlite3.Row) -> tuple[ImpostazioniSalvate, tuple[str, ...]]:
    """Parse a stored row defensively: an unreadable `valori` falls back to `FABBRICA` merged with
    every key that still validates, never raising."""
    valori, avvisi = _valori_o_fabbrica(row["valori"], row["revisione"])
    salvate = ImpostazioniSalvate(
        valori=valori, revisione=row["revisione"], sigla=row["sigla"], aggiornato_il=row["aggiornato_il"]
    )
    return salvate, avvisi


def _valori_o_fabbrica(raw: str, revisione: int) -> tuple[Impostazioni, tuple[str, ...]]:
    try:
        return Impostazioni.model_validate_json(raw), ()
    except (ValueError, TypeError):
        pass
    try:
        parziale = json.loads(raw)
    except (ValueError, TypeError):
        parziale = {}
    campi_validi: dict = {}
    for chiave, valore in (parziale.items() if isinstance(parziale, dict) else ()):
        try:
            Impostazioni.model_validate({**FABBRICA.model_dump(), chiave: valore})
            campi_validi[chiave] = valore
        except ValueError:
            continue
    logger.warning("impostazioni revisione %s non leggibili: uso i valori di fabbrica dove serve", revisione)
    fusi = Impostazioni.model_validate({**FABBRICA.model_dump(), **campi_validi})
    campi_persi = sorted(set(FABBRICA.model_dump()) - set(campi_validi))
    return fusi, (_AVVISO_CORROTTO.format(campi=", ".join(campi_persi) or "tutti i valori"),) if campi_persi else ()


class SqliteImpostazioniRepository:
    """Implements `ImpostazioniRepository` against a SQLite file at `db_path`."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def leggi(self) -> ImpostazioniSalvate:
        salvate, _ = self.leggi_con_avvisi()
        return salvate

    def leggi_con_avvisi(self) -> tuple[ImpostazioniSalvate, tuple[str, ...]]:
        with session(self._db_path) as connection:
            row = connection.execute("SELECT * FROM impostazioni WHERE id = 1").fetchone()
        if row is None:
            return ImpostazioniSalvate(), ()
        return _row_to_salvate(row)

    def salva(self, valori: Impostazioni, revisione_attesa: int, sigla: str) -> ImpostazioniSalvate:
        with write_session(self._db_path) as connection:
            row = connection.execute("SELECT revisione FROM impostazioni WHERE id = 1").fetchone()
            attuale = row["revisione"] if row is not None else 0
            if attuale != revisione_attesa:
                raise ConflictError("impostazioni modificate nel frattempo")
            record = ImpostazioniSalvate(
                valori=valori, revisione=attuale + 1, sigla=sigla, aggiornato_il=_utc_now_iso()
            )
            payload = {
                "valori": record.valori.model_dump_json(),
                "revisione": record.revisione,
                "sigla": record.sigla,
                "aggiornato_il": record.aggiornato_il,
            }
            connection.execute(
                """
                INSERT INTO impostazioni (id, valori, revisione, sigla, aggiornato_il) VALUES (1, :valori, :revisione, :sigla, :aggiornato_il)
                ON CONFLICT(id) DO UPDATE SET
                    valori = excluded.valori, revisione = excluded.revisione, sigla = excluded.sigla,
                    aggiornato_il = excluded.aggiornato_il
                """,
                payload,
            )
            connection.execute(
                """
                INSERT INTO impostazioni_storia (revisione, valori, sigla, aggiornato_il)
                VALUES (:revisione, :valori, :sigla, :aggiornato_il)
                """,
                payload,
            )
        return record

    def storia(self, limite: int = 50) -> tuple[ImpostazioniSalvate, ...]:
        with session(self._db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM impostazioni_storia ORDER BY revisione DESC LIMIT ?", (limite,)
            ).fetchall()
        return tuple(_row_to_salvate(row)[0] for row in rows)


def open_impostazioni_repository(data_dir: Path) -> SqliteImpostazioniRepository:
    """Run migrations against `<data_dir>/strutture.db` and return a ready repository."""
    db_path = data_dir / DB_FILENAME
    with session(db_path) as connection:
        migrate(connection)
    return SqliteImpostazioniRepository(db_path)

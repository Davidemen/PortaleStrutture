"""In-memory ProjectRepository with identical behaviour to the SQLite one, for other packages' tests."""
from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime

from .interfaces import ConflictError, NotFoundError
from .models import Elemento, Progetto, RevisioneElemento


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id() -> str:
    return uuid.uuid4().hex


def _check_revisione(current: int, expected: int) -> None:
    if current != expected:
        raise ConflictError(f"revisione attesa {expected}, trovata {current}")


class InMemoryProjectRepository:
    """Thread-safe, process-local `ProjectRepository`. Nothing is persisted across instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._progetti: dict[str, Progetto] = {}
        self._elementi: dict[str, Elemento] = {}
        self._revisioni: dict[str, tuple[RevisioneElemento, ...]] = {}

    # ---- progetti ----

    def list_progetti(self, *, inclusi_eliminati: bool = False) -> tuple[Progetto, ...]:
        with self._lock:
            items = list(self._progetti.values())
        if not inclusi_eliminati:
            items = [item for item in items if item.eliminato == ""]
        return tuple(sorted(items, key=lambda p: (p.aggiornato, p.id), reverse=True))

    def get_progetto(self, progetto_id: str) -> Progetto:
        with self._lock:
            progetto = self._progetti.get(progetto_id)
        if progetto is None:
            raise NotFoundError(progetto_id)
        return progetto

    def crea_progetto(self, progetto: Progetto) -> Progetto:
        now = _utc_now_iso()
        record = progetto.model_copy(update={"id": _new_id(), "revisione": 1, "creato": now, "aggiornato": now,
                                              "eliminato": ""})
        with self._lock:
            self._progetti[record.id] = record
        return record

    def aggiorna_progetto(self, progetto: Progetto) -> Progetto:
        with self._lock:
            current = self._progetti.get(progetto.id)
            if current is None or current.eliminato != "":
                raise NotFoundError(progetto.id)
            _check_revisione(current.revisione, progetto.revisione)
            record = progetto.model_copy(update={"revisione": current.revisione + 1, "creato": current.creato,
                                                  "aggiornato": _utc_now_iso(), "eliminato": current.eliminato})
            self._progetti[record.id] = record
        return record

    def elimina_progetto(self, progetto_id: str, revisione: int) -> None:
        with self._lock:
            current = self._progetti.get(progetto_id)
            if current is None or current.eliminato != "":
                raise NotFoundError(progetto_id)
            _check_revisione(current.revisione, revisione)
            now = _utc_now_iso()
            self._progetti[progetto_id] = current.model_copy(
                update={"eliminato": now, "aggiornato": now, "revisione": current.revisione + 1}
            )

    def ripristina_progetto(self, progetto_id: str) -> Progetto:
        with self._lock:
            current = self._progetti.get(progetto_id)
            if current is None:
                raise NotFoundError(progetto_id)
            record = current.model_copy(
                update={"eliminato": "", "aggiornato": _utc_now_iso(), "revisione": current.revisione + 1}
            )
            self._progetti[progetto_id] = record
        return record

    # ---- elementi ----

    def list_elementi(self, progetto_id: str, *, inclusi_eliminati: bool = False) -> tuple[Elemento, ...]:
        with self._lock:
            items = [e for e in self._elementi.values() if e.progetto_id == progetto_id and (inclusi_eliminati or e.eliminato == "")]
        return tuple(sorted(items, key=lambda e: (e.aggiornato, e.id), reverse=True))

    def get_elemento(self, elemento_id: str) -> Elemento:
        with self._lock:
            elemento = self._elementi.get(elemento_id)
        if elemento is None:
            raise NotFoundError(elemento_id)
        return elemento

    def crea_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        now = _utc_now_iso()
        record = elemento.model_copy(update={"id": _new_id(), "revisione": 1, "creato": now, "aggiornato": now,
                                              "eliminato": ""})
        with self._lock:
            self._elementi[record.id] = record
            self._append_revisione(record, sigla, nota, now)
        return record

    def aggiorna_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        with self._lock:
            current = self._elementi.get(elemento.id)
            if current is None or current.eliminato != "":
                raise NotFoundError(elemento.id)
            _check_revisione(current.revisione, elemento.revisione)
            now = _utc_now_iso()
            record = elemento.model_copy(update={"revisione": current.revisione + 1, "creato": current.creato,
                                                  "aggiornato": now, "eliminato": current.eliminato})
            self._elementi[record.id] = record
            self._append_revisione(record, sigla, nota, now)
        return record

    def duplica_elemento(self, elemento_id: str, nuovo_nome: str) -> Elemento:
        with self._lock:
            source = self._elementi.get(elemento_id)
            if source is None or source.eliminato != "":
                raise NotFoundError(elemento_id)
            now = _utc_now_iso()
            record = source.model_copy(update={"id": _new_id(), "nome": nuovo_nome, "revisione": 1, "creato": now,
                                                "aggiornato": now, "eliminato": ""})
            self._elementi[record.id] = record
            self._append_revisione(record, "", "", now)
        return record

    def elimina_elemento(self, elemento_id: str, revisione: int) -> None:
        with self._lock:
            current = self._elementi.get(elemento_id)
            if current is None or current.eliminato != "":
                raise NotFoundError(elemento_id)
            _check_revisione(current.revisione, revisione)
            now = _utc_now_iso()
            self._elementi[elemento_id] = current.model_copy(
                update={"eliminato": now, "aggiornato": now, "revisione": current.revisione + 1}
            )

    def ripristina_elemento(self, elemento_id: str) -> Elemento:
        with self._lock:
            current = self._elementi.get(elemento_id)
            if current is None:
                raise NotFoundError(elemento_id)
            now = _utc_now_iso()
            record = current.model_copy(update={"eliminato": "", "aggiornato": now, "revisione": current.revisione + 1})
            self._elementi[elemento_id] = record
        return record

    def revisioni(self, elemento_id: str) -> tuple[RevisioneElemento, ...]:
        with self._lock:
            return self._revisioni.get(elemento_id, ())

    def _append_revisione(self, elemento: Elemento, sigla: str, nota: str, now: str) -> None:
        entry = RevisioneElemento(
            elemento_id=elemento.id,
            revisione=elemento.revisione,
            inputs=elemento.inputs,
            sintesi=elemento.sintesi,
            sigla=sigla,
            nota=nota,
            data=now,
        )
        self._revisioni[elemento.id] = self._revisioni.get(elemento.id, ()) + (entry,)

"""In-memory ImpostazioniRepository with identical behaviour to the SQLite one, for tests."""
from __future__ import annotations

import threading
from datetime import UTC, datetime

from strutture.shared.impostazioni.modelli import Impostazioni, ImpostazioniSalvate

from .interfaces import ConflictError


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class InMemoryImpostazioniRepository:
    """Thread-safe, process-local `ImpostazioniRepository`. Nothing is persisted across instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current = ImpostazioniSalvate()
        self._storia: tuple[ImpostazioniSalvate, ...] = ()

    def leggi(self) -> ImpostazioniSalvate:
        with self._lock:
            return self._current

    def salva(self, valori: Impostazioni, revisione_attesa: int, sigla: str) -> ImpostazioniSalvate:
        with self._lock:
            if self._current.revisione != revisione_attesa:
                raise ConflictError("impostazioni modificate nel frattempo")
            record = ImpostazioniSalvate(
                valori=valori, revisione=self._current.revisione + 1, sigla=sigla, aggiornato_il=_utc_now_iso()
            )
            self._current = record
            self._storia = (record, *self._storia)
        return record

    def storia(self, limite: int = 50) -> tuple[ImpostazioniSalvate, ...]:
        with self._lock:
            return self._storia[:limite]

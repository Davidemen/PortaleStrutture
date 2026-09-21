"""In-memory SignoffRepository with identical behaviour to the SQLite one, for other packages' tests."""
from __future__ import annotations

import threading
from datetime import UTC, datetime

from .models import Signoff, Stato


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class InMemorySignoffRepository:
    """Thread-safe, process-local `SignoffRepository`. Nothing is persisted across instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current: dict[str, Signoff] = {}
        self._history: dict[str, tuple[Signoff, ...]] = {}

    def get(self, divergence_id: str) -> Signoff:
        with self._lock:
            return self._current.get(divergence_id, Signoff(divergence_id=divergence_id))

    def list_all(self) -> dict[str, Signoff]:
        with self._lock:
            return dict(self._current)

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        record = Signoff(divergence_id=divergence_id, stato=stato, sigla=sigla, nota=nota, data=_utc_now_iso())
        with self._lock:
            self._current[divergence_id] = record
            self._history[divergence_id] = self._history.get(divergence_id, ()) + (record,)
        return record

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        with self._lock:
            return self._history.get(divergence_id, ())

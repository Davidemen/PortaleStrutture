"""Repository interfaces. Business code and routes depend on these Protocols, never on sqlite3."""
from typing import Protocol

from .models import Signoff, Stato


class SignoffRepository(Protocol):
    def get(self, divergence_id: str) -> Signoff:
        """Current decision; a never-decided id returns Signoff(stato='da_confermare')."""
        ...

    def list_all(self) -> dict[str, Signoff]:
        """Current decision of every id that was ever decided."""
        ...

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        """Record a decision (appends to the history) and return the stored record."""
        ...

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        """Every decision ever recorded for the id, oldest first."""
        ...

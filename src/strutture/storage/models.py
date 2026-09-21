"""Records stored by the app. Frozen; timestamps are ISO-8601 UTC strings."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Stato = Literal["da_confermare", "approvato", "respinto"]
MAX_SIGLA = 12
MAX_NOTA = 2000


class Signoff(BaseModel):
    """The engineer's decision on one divergence. No accounts: `sigla` is whatever the engineer types."""

    model_config = ConfigDict(frozen=True)

    divergence_id: str
    stato: Stato = "da_confermare"
    sigla: str = Field(default="", max_length=MAX_SIGLA)
    nota: str = Field(default="", max_length=MAX_NOTA)
    data: str = ""  # ISO-8601 UTC, set by the repository

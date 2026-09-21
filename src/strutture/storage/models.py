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


# ---- Phase 3: projects and saved elements (no user management: everyone can read and edit everything) ----
StatoElemento = Literal["verificato", "non_verificato", "dati_modificati"]
MAX_NOME = 120
MAX_NOTE = 4000


class Progetto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = ""                      # uuid4 hex, set by the repository
    codice: str = Field(default="", max_length=40)       # office job number, free text
    nome: str = Field(min_length=1, max_length=MAX_NOME)
    committente: str = Field(default="", max_length=MAX_NOME)
    note: str = Field(default="", max_length=MAX_NOTE)
    revisione: int = 0                # optimistic-locking counter, +1 on every update
    creato: str = ""
    aggiornato: str = ""
    eliminato: str = ""               # soft delete timestamp ("" = active)


class Elemento(BaseModel):
    """One saved calculation ("Plinto P1"): a tool + its inputs + a summary of the last result."""

    model_config = ConfigDict(frozen=True)

    id: str = ""
    progetto_id: str
    strumento: str                    # tool name
    nome: str = Field(min_length=1, max_length=MAX_NOME)
    inputs: dict = Field(default_factory=dict)            # exactly what the tool form submits
    sintesi: dict = Field(default_factory=dict)           # {ok, eta_max, verifica_governante, evidenze: [...]} for lists
    stato: StatoElemento = "non_verificato"
    modalita: Literal["standard", "excel"] = "standard"
    versione_app: str = ""
    provenienza: dict = Field(default_factory=dict)       # e.g. MIDAS import: {fonte, modello, unita, n_righe, data}
    revisione: int = 0
    creato: str = ""
    aggiornato: str = ""
    eliminato: str = ""


class RevisioneElemento(BaseModel):
    """Append-only history entry written on every save of an element."""

    model_config = ConfigDict(frozen=True)

    elemento_id: str
    revisione: int
    inputs: dict
    sintesi: dict
    sigla: str = Field(default="", max_length=MAX_SIGLA)
    nota: str = Field(default="", max_length=MAX_NOTA)
    data: str = ""

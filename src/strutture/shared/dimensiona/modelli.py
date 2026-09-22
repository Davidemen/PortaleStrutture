"""Frozen pydantic request/response models for `/dimensiona` and `/sensibilita` (WORKBENCH_SPEC
§23.4, §24.1)."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .serie import MAX_PUNTI


class CorpoDimensiona(BaseModel):
    model_config = ConfigDict(frozen=True)

    inputs: dict[str, Any]
    campo: str
    da: float
    a: float
    passo: float
    obiettivo: float = Field(gt=0, le=1)
    verso: Literal["auto", "minimo", "massimo"] = "auto"


class CampioneRisposta(BaseModel):
    model_config = ConfigDict(frozen=True)

    valore: float
    esito: Literal["ammissibile", "non_ammissibile", "errore"]
    eta_max: float | None = None
    messaggio: str = ""
    avvisi_nuovi: tuple[str, ...] = ()


class Correzioni(BaseModel):
    model_config = ConfigDict(frozen=True)

    da_confermare: int = 0
    respinto: int = 0


class Governante(BaseModel):
    model_config = ConfigDict(frozen=True)

    nome: str
    eta: float


class RispostaDimensiona(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool = True
    campo: str
    verso: Literal["minimo", "massimo"]
    esito: Literal["trovato", "estremo_sufficiente", "nessun_valore", "interrotta", "limite_validita"]
    valore: float | None
    affidabile: bool
    motivi: tuple[str, ...]
    governante: Governante | None
    verifiche_solo_esito: tuple[str, ...]
    verifiche_senza_obiettivo: tuple[str, ...]
    campioni: tuple[CampioneRisposta, ...]
    valutazioni: int
    durata_s: float
    modalita: Literal["standard", "excel"]
    correzioni: Correzioni
    obiettivo: float
    passo: float
    obiettivo_su_minimi: bool
    report: dict[str, Any] | None


class CorpoSensibilita(BaseModel):
    model_config = ConfigDict(frozen=True)

    inputs: dict[str, Any]
    campo: str
    da: float
    a: float
    punti: int = Field(ge=2, le=MAX_PUNTI)


class VoceVerificaRisposta(BaseModel):
    model_config = ConfigDict(frozen=True)

    nome: str
    clausola: str
    eta: tuple[float | None, ...]
    esito: tuple[bool | None, ...]


class ErroreSerie(BaseModel):
    model_config = ConfigDict(frozen=True)

    valore: float
    messaggio: str


class RispostaSensibilita(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool = True
    campo: str
    valori: tuple[float, ...]
    verifiche: tuple[VoceVerificaRisposta, ...]
    errori: tuple[ErroreSerie, ...]
    verifiche_solo_esito: tuple[str, ...]
    modalita: Literal["standard", "excel"]
    correzioni: Correzioni
    completa: bool

"""Single implementation of the NTC 2018 partial-factor combination tables (Tab. 6.2.I/6.2.II/6.5.I),
shared by every tool that composes STR/GEO/EQU combinations (today: `members.muro`). Pure typed
data + lookup functions only; no `Tool` is registered here."""
from .lookup import fattori_azioni, fattori_geotecnici, fattori_resistenza
from .models import (
    ApproccioAzioni,
    ApproccioGeotecnico,
    ApproccioResistenza,
    FattoriAzioni,
    FattoriGeotecnici,
    FattoriResistenza,
    VerificaOpereDiSostegno,
)

__all__ = [
    "ApproccioAzioni",
    "ApproccioGeotecnico",
    "ApproccioResistenza",
    "FattoriAzioni",
    "FattoriGeotecnici",
    "FattoriResistenza",
    "VerificaOpereDiSostegno",
    "fattori_azioni",
    "fattori_geotecnici",
    "fattori_resistenza",
]

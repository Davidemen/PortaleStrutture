"""Lookups over the NTC2018 §6.2/§6.5 partial-factor tables (pure, no I/O)."""
from strutture.shared.tables import exact_lookup

from .models import (
    ApproccioAzioni,
    ApproccioGeotecnico,
    FattoriAzioni,
    FattoriGeotecnici,
    FattoriResistenza,
    VerificaOpereDiSostegno,
)
from .tables import FATTORI_AZIONI, FATTORI_GEOTECNICI, FATTORI_RESISTENZA


def fattori_azioni(approccio: ApproccioAzioni) -> FattoriAzioni:
    """Tab. 6.2.I row for the given approccio (EQU/A1/A2)."""
    return exact_lookup(FATTORI_AZIONI, approccio)


def fattori_geotecnici(approccio: ApproccioGeotecnico) -> FattoriGeotecnici:
    """Tab. 6.2.II row for the given approccio geotecnico (M1/M2)."""
    return exact_lookup(FATTORI_GEOTECNICI, approccio)


def fattori_resistenza(verifica: VerificaOpereDiSostegno) -> FattoriResistenza:
    """Tab. 6.5.I row (γR1/γR2/γR3) for the given verifica delle opere di sostegno."""
    return exact_lookup(FATTORI_RESISTENZA, verifica)

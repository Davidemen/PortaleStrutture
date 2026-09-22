"""Frozen output models for `acciaio-colonna-h-ec3`, grouped as in acciaio-colonne-ec3!Column check.

Entry point re-exporting the group models (split into `results_*.py` files for regola dura 12,
module size); every other module in this package imports from here.
"""
from pydantic import BaseModel, ConfigDict

from strutture.shared.sketch import Sketch, campo_schizzo

from .results_instabilita import InstabilitaFlessionale, InstabilitaTorsoFlessionale
from .results_interazione import Interazione, InterazioneSemplificata
from .results_resistenza import Flessione, Taglio, TaglioInstabilita
from .results_sezione import Materiali, Sezione

__all__ = [
    "ColonnaEc3Output",
    "Flessione",
    "InstabilitaFlessionale",
    "InstabilitaTorsoFlessionale",
    "Interazione",
    "InterazioneSemplificata",
    "Materiali",
    "Sezione",
    "Taglio",
    "TaglioInstabilita",
]


class ColonnaEc3Output(BaseModel):
    """Esito completo della verifica di colonna in acciaio a sezione H/I, EN1993-1-1."""

    model_config = ConfigDict(frozen=True)

    materiali: Materiali
    sezione: Sezione
    instabilita_flessionale: InstabilitaFlessionale
    instabilita_torso_flessionale: InstabilitaTorsoFlessionale
    flessione: Flessione
    taglio: Taglio
    taglio_instabilita: TaglioInstabilita
    interazione: Interazione
    interazione_semplificata: InterazioneSemplificata
    schizzo: Sketch | None = campo_schizzo()

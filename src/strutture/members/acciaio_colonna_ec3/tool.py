"""Tool registration: acciaio-colonna-h-ec3 — H/I-section steel column, EN1993-1-1.

One composed `Tool` for the whole sheet (acciaio-colonne-ec3!Column check); `run` (every step module
wired together) lives in `compose.py`, re-exported here (regola dura 12, module size).
"""
from strutture.shared.tool import Tool

from .compose import run
from .esempio import ESEMPIO_AUREO, ESEMPIO_TOOL
from .models import ColonnaEc3Input
from .relazione import relazione as relazione_colonna_ec3
from .results import ColonnaEc3Output

__all__ = ["ESEMPIO_AUREO", "TOOLS", "run"]

TOOLS = (
    Tool(
        name="acciaio-colonna-h-ec3",
        title="Verifica di instabilità e resistenza colonne ad H/I — EC3",
        group="Acciaio / Colonne",
        norm="EN1993-1-1 §5.5, §6.2, §6.3",
        input_model=ColonnaEc3Input,
        output_model=ColonnaEc3Output,
        run=run,
        example=ESEMPIO_TOOL,
        summary="Verifica la resistenza e la stabilità di una colonna in acciaio a sezione H/I soggetta a sforzo normale e flessione biassiale.",
        relazione=relazione_colonna_ec3,
    ),
)

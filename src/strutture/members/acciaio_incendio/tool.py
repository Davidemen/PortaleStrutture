"""`acciaio-resistenza-incendio` — steel strength/stiffness reduction in fire (EN1993-1-2 §3.2.1,
Table 3.1) for a grade and a list of ISO 834 exposure times."""
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tables import KeyNotFound
from strutture.shared.tool import Tool

from .models import ResistenzaIncendioInput, ResistenzaIncendioOutput
from .righe import riga_resistenza_incendio
from .steel_base import materiale_base

# Example inputs (default mode): the golden case of docs/specs/acciaio.md §"Tool 2" at t = 5 min.
ESEMPIO = {"grado": "S355", "tempi_min": [5.0]}

NO_THERMAL_LAG_WARNING = (
    "Il foglio assume acciaio non protetto e trascura l'inerzia termica della sezione: la "
    "temperatura dell'acciaio è posta uguale a quella del gas (curva ISO 834), senza fattore di "
    "sezione Am/V né protezione — risultato semplificato, non un'analisi termica completa "
    "EN1991-1-2."
)


def run(inputs: ResistenzaIncendioInput) -> Report[ResistenzaIncendioOutput]:
    materiale = materiale_base(inputs.grado, legacy_compat=inputs.legacy_compat)
    try:
        righe = tuple(
            riga_resistenza_incendio(t_min, materiale, inputs.e_20_MPa) for t_min in inputs.tempi_min
        )
    except KeyNotFound as error:
        raise CalcError(
            f"Tempo di esposizione fuori dal campo di validità della Tab. 3.1 EN1993-1-2: {error}"
        ) from error
    data = ResistenzaIncendioOutput(materiale=materiale, righe=righe)
    return success(data, inputs, warnings=(NO_THERMAL_LAG_WARNING,))


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="acciaio-resistenza-incendio",
        title="Acciaio — resistenza e rigidezza in condizioni di incendio",
        group="Acciaio / Fuoco",
        norm="EN1993-1-2 §3.2.1, Tab. 3.1",
        input_model=ResistenzaIncendioInput,
        output_model=ResistenzaIncendioOutput,
        run=run,
        example=ESEMPIO,
    ),
)

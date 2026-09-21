"""`acciaio-proprieta-temperatura` — structural steel material properties reduced at a given
steel temperature θ (EN1993-1-2 §3.2.1, Tab. 3.1)."""
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .proprieta import proprieta_a_temperatura
from .proprieta_models import ProprietaTemperaturaInput, ProprietaTemperaturaOutput

# Golden case: docs/specs/small-units.md §"Golden test case", θ=550°C (interpolated, not on a
# Table 3.1 node) — default mode, no legacy_compat (DESIGN_SPEC §4).
ESEMPIO = {"fyk_MPa": 355.0, "ea_20_MPa": 210000.0, "theta_C": 550.0}


def run(inputs: ProprietaTemperaturaInput) -> Report[ProprietaTemperaturaOutput]:
    data = proprieta_a_temperatura(inputs)
    return success(data, inputs)


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="acciaio-proprieta-temperatura",
        title="Acciaio — proprietà del materiale a temperatura",
        group="Acciaio / Fuoco",
        norm="EN1993-1-2 §3.2.1, Tab. 3.1",
        input_model=ProprietaTemperaturaInput,
        output_model=ProprietaTemperaturaOutput,
        run=run,
        example=ESEMPIO,
    ),
)

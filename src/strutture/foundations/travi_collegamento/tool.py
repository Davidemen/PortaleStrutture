"""Tool registration: `fond-trave-collegamento` — one composed tool, `norma` switches the
NTC2018/EN1998 branch (architecture-batch2.md §1 `foundations/travi_collegamento`)."""
from strutture.shared.report import Report
from strutture.shared.tool import Tool

from .models import TraviCollegamentoInput
from .output import TraviCollegamentoOutput
from .tool_en import run_en
from .tool_ntc import run_ntc

ESEMPIO_NTC2018 = {
    "norma": "NTC2018", "ag_g": 0.151, "f0": 2.43, "categoria_sottosuolo": "B", "categoria_topografica": "T1",
    "b_mm": 400, "h_mm": 400, "phi_mm": 16, "n_barre": 6, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "phi_staffa_mm": 10, "n_bracci": 2, "cf_mm": 40, "p_mm": 125,
}


def run(inputs: TraviCollegamentoInput) -> Report[TraviCollegamentoOutput]:
    """Dispatch to the NTC2018 or EN1998 branch per `inputs.norma`."""
    return run_ntc(inputs) if inputs.norma == "NTC2018" else run_en(inputs)


TOOLS = (
    Tool(
        name="fond-trave-collegamento",
        title="Verifica trave di collegamento tra plinti (NTC2018 / EN1998)",
        group="Fondazioni / Travi di collegamento",
        norm="NTC2018 §7.2.5 / EN1998-1 §5.8.2 / EN1998-5 §5.4.1.2",
        input_model=TraviCollegamentoInput,
        output_model=TraviCollegamentoOutput,
        run=run,
        example=ESEMPIO_NTC2018,
        summary="Verifica la trave di collegamento tra due plinti a compressione, trazione, snellezza e staffe minime.",
    ),
)

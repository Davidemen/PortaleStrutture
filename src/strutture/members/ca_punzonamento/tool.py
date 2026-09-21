"""Tool registration: ca-punzonamento (EN 1992-1-1 §6.4, punching shear + §9.4.3 detailing)."""
from strutture.shared.tool import Tool

from .compose import run
from .models import PunzonamentoInput, PunzonamentoOutput
from .relazione import relazione

# docs/specs/ca-punzonamento.md §8 golden case (Shotblast_225N).
EXAMPLE = {
    "ved_kN": 225, "pterreno_MPa": 0, "lato_a_mm": 400, "lato_b_mm": 400, "h_mm": 500, "diametro_mm": 0,
    "fck_MPa": 35, "copriferro_mm": 50, "posizione": "interno", "px_mm": 200, "py_mm": 200, "phix_mm": 20,
    "phiy_mm": 20, "a1eff_mm": 400, "bu_mm": 380, "st_mm": 200, "phi_staffa_mm": 12, "n_staffe": 8,
}

TOOLS = (
    Tool(
        name="ca-punzonamento",
        title="Verifica a punzonamento e progetto armature verticali (solai/platee su pilastri o pali)",
        group="Calcestruzzo armato / Punzonamento",
        norm="EN 1992-1-1 §6.4",
        input_model=PunzonamentoInput,
        output_model=PunzonamentoOutput,
        run=run,
        example=EXAMPLE,
        summary="Verifica a punzonamento di un solaio o platea su pilastro o palo e progetta le armature verticali se necessarie.",
        relazione=relazione,
    ),
)

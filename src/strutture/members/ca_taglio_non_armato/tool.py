"""Registration of the composed tool `ca-taglio-non-armato` (RC section shear capacity without
transverse reinforcement, NTC2018 §4.1.2.3.5.1). Covers both workbook sheets through the same
flat input model: `Foglio1` (v1: fck derived from Rck, Asl given directly) and `1m` (v2: fck given
directly, Asl given as N°/Ø of longitudinal bars, per-metre-strip convention) — see `compose.py`
and `models.py` for the delta handling."""
from strutture.shared.tool import Tool

from .compose import run
from .models import TaglioNonArmatoInput, TaglioNonArmatoOutput
from .relazione import relazione

ESEMPIO_AUREO = {
    "rck_MPa": 35, "h_mm": 500, "c_mm": 50, "bw_mm": 1000, "asl_mm2": 1005, "ned_kN": 0,
}

TOOLS = (
    Tool(
        name="ca-taglio-non-armato",
        title="Resistenza a taglio di sezione in c.a. priva di armatura trasversale",
        group="Calcestruzzo armato / Travi",
        norm="NTC2018 §4.1.2.3.5.1",
        input_model=TaglioNonArmatoInput,
        output_model=TaglioNonArmatoOutput,
        run=run,
        example=ESEMPIO_AUREO,
        summary="Verifica la resistenza a taglio di una sezione in c.a. priva di armatura trasversale.",
        relazione=relazione,
    ),
)

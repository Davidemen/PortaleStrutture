"""Tool registration: pilastro-rettangolare and pilastro-circolare (NTC2018 §4.1/§7.4, CD "B")."""
from strutture.shared.tool import Tool

from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .relazione import relazione_circolare, relazione_rettangolare
from .tool_circolare import run_pilastro_circolare
from .tool_rettangolare import run_pilastro_rettangolare

ESEMPIO_RETTANGOLARE = {
    "l1_mm": 400, "l2_mm": 400, "h_mm": 3500, "acciaio": "B450C", "cls": "C25/30",
    "ned_kN": 1200, "ved_kN": 150, "med_kNm": 80, "c_mm": 50, "n_ferri": 8,
    "diametro_ferri_mm": 16, "diametro_staffe_mm": 10, "passo_staffe_mm": 150,
    "mrd_kNm": 160, "n_ferri_l1": 3,
}
ESEMPIO_CIRCOLARE = {
    "d_mm": 400, "h_mm": 5000, "acciaio": "B450C", "cls": "C25/30",
    "ned_kN": 1200, "ved_kN": 150, "med_kNm": 80, "c_mm": 50, "n_ferri": 25,
    "diametro_ferri_mm": 16, "diametro_staffe_mm": 10, "passo_staffe_mm": 150,
    "mrd_kNm": 160,
}

_NORM = (
    "NTC2018 §4.1/§7.4 + Circolare 7/2019; norma=EC2 -> UNI EN 1992-1-1:2005 con Allegato "
    "Nazionale italiano (α_cc=0.85); norma=NTC2008 -> solo riproduzione del foglio Excel "
    "originale (richiede legacy_compat=True)"
)

TOOLS = (
    Tool(
        name="ca-pilastro-rettangolare",
        title="Verifica pilastro in c.a. rettangolare/quadrato (CD \"B\")",
        group="Calcestruzzo armato / Pilastri",
        norm=_NORM,
        input_model=PilastroRettangolareInput,
        output_model=PilastroOutput,
        run=run_pilastro_rettangolare,
        example=ESEMPIO_RETTANGOLARE,
        summary="Verifica un pilastro in c.a. a sezione rettangolare a pressoflessione, taglio, snellezza e dettagli sismici.",
        relazione=relazione_rettangolare,
    ),
    Tool(
        name="ca-pilastro-circolare",
        title="Verifica pilastro in c.a. circolare (CD \"B\")",
        group="Calcestruzzo armato / Pilastri",
        norm=_NORM,
        input_model=PilastroCircolareInput,
        output_model=PilastroOutput,
        run=run_pilastro_circolare,
        example=ESEMPIO_CIRCOLARE,
        summary="Verifica un pilastro in c.a. a sezione circolare a pressoflessione, taglio, snellezza e dettagli sismici.",
        relazione=relazione_circolare,
    ),
)

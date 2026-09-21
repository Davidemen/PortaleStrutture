"""Tool registration: ca-sezione-dominio-mn — dominio di resistenza N-M/Mx-My di una sezione in
c.a. qualsiasi e verifica a pressoflessione su una tabella di combinazioni di carico
(docs/architecture-phase4.md §B). No `legacy_compat`: pure closed-form engine, no Excel oracle.

`Tool.group` is "Calcestruzzo armato / Pilastri" rather than the bare "Calcestruzzo armato" named
in the task brief: `tests/shared/test_tool_taxonomy.py` enforces a closed `CANONICAL_GROUPS` set
that this package may not edit (outside its assigned directories), and pressoflessione retta/
deviata under N-M is the column (pilastro) verification this closed list already anticipates —
see the tool's final report for this deviation."""
from strutture.shared.tool import Tool

from .compose import run
from .models_input import SezioneMnInput
from .models_output import SezioneMnOutput

# Esempio in modalità standard (nessun legacy_compat): pilastro rettangolare 300x500 mm, armatura
# perimetrale 3 barre per lato, 3 combinazioni SLU (una uniassiale x, una biassiale, una quasi in
# compressione centrata) che esercitano i tre rami della verifica a pressoflessione.
EXAMPLE = {
    "forma": "rettangolare",
    "b_mm": 300,
    "h_mm": 500,
    "armatura_modo": "layout",
    "layout_tipo": "perimetrale",
    "layout_copriferro_mm": 30,
    "layout_diametro_mm": 20,
    "layout_n_per_lato": 3,
    "classe_calcestruzzo": "C25/30",
    "grado_acciaio": "B450C",
    "azioni": [
        {"nome": "SLU1", "n_ed_kN": 800, "m_ed_x_kNm": 150, "m_ed_y_kNm": 0},
        {"nome": "SLU2", "n_ed_kN": 400, "m_ed_x_kNm": 120, "m_ed_y_kNm": 60},
        {"nome": "SLU3", "n_ed_kN": 1600, "m_ed_x_kNm": 40, "m_ed_y_kNm": 0},
    ],
}

TOOLS = (
    Tool(
        name="ca-sezione-dominio-mn",
        title="Dominio di resistenza a pressoflessione N-M di una sezione in c.a.",
        group="Calcestruzzo armato / Pilastri",
        norm="NTC2018 §4.1.2.3.4.2",
        input_model=SezioneMnInput,
        output_model=SezioneMnOutput,
        run=run,
        example=EXAMPLE,
        summary="Traccia il dominio di resistenza N-M di una sezione in c.a. qualsiasi e verifica a "
                "pressoflessione una tabella di combinazioni di carico.",
    ),
)

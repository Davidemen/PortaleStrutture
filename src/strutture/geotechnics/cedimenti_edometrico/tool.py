"""Tool registration: `geo-cedimento-edometrico` (docs/specs/geo-cedimenti-edometrico.md,
docs/architecture-batch2.md §1 `geotechnics/cedimenti_edometrico`). `run` only composes the step
modules; no calculation lives here."""
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tables import KeyNotFound
from strutture.shared.tool import Tool

from .carico import pressione_netta
from .cedimento import cedimento_totale
from .ingresso import converti_in_si
from .models import EdometricoInput, MetodoTensioni
from .output import EdometricoOutput
from .profondita_critica import profondita_critica
from .righe import genera_righe

# docs/specs/geo-cedimenti-edometrico.md "Golden test case" (sheet Edometrico, cached run):
# B=350 cm, L=500 cm, γ=1800 kg/mc, q=0.5 kg/cmq, D=0, Z,crit=10000 cm (disabled), 5 layers.
ESEMPIO = {
    "sistema_unita": "tecnico",
    "b": 350, "l": 500, "d": 0, "gamma": 1800, "q": 0.5,
    "strati": [
        {"z_top_m": 0.00, "z_bot_m": 3.70, "modulo_MPa": 5.500000812600001},
        {"z_top_m": 3.70, "z_bot_m": 4.70, "modulo_MPa": 6.99999657665},
        {"z_top_m": 4.70, "z_bot_m": 5.50, "modulo_MPa": 9.00000400425},
        {"z_top_m": 5.50, "z_bot_m": 31.50, "modulo_MPa": 6.99999657665},
        {"z_top_m": 31.50, "z_bot_m": 118.90, "modulo_MPa": 6.99999657665},
    ],
    "metodo_tensioni": "approssimato",
    "z_crit_input": 10000,
    "dz": 10,
    "z_max": 5000,
}


def run(inputs: EdometricoInput) -> Report[EdometricoOutput]:
    si = converti_in_si(inputs)
    metodo: MetodoTensioni = "approssimato" if inputs.legacy_compat else inputs.metodo_tensioni
    # legacy_compat=True stays frozen on the sheet's own formulas: embedment/water table ignored
    # for σ'v0 and Z,crit (docs/architecture-batch2.md §7 review finding HIGH; divergence docs).
    d_m_sigma = 0.0 if inputs.legacy_compat else si.d_m
    water_table_m_sigma = 0.0 if inputs.legacy_compat else si.falda_m
    carico = pressione_netta(
        si.q_kPa, si.gamma_kN_m3, si.d_m, water_table_m=si.falda_m, legacy_compat=inputs.legacy_compat,
    )
    try:
        righe = genera_righe(
            carico.q_prime_kPa, si.b_m, si.l_m, si.gamma_kN_m3, inputs.strati,
            metodo=metodo, dz_m=si.dz_m, z_max_m=si.z_max_m, legacy_compat=inputs.legacy_compat,
            d_m=d_m_sigma, water_table_m=water_table_m_sigma,
        )
    except KeyNotFound as errore:
        raise CalcError(str(errore)) from errore
    profondita = profondita_critica(
        carico.q_prime_kPa, si.b_m, si.l_m, si.gamma_kN_m3, metodo=metodo,
        z_crit_input_m=si.z_crit_input_m, legacy_compat=inputs.legacy_compat, z_max_m=si.z_max_m,
        d_m=d_m_sigma, water_table_m=water_table_m_sigma,
    )
    cedimento = cedimento_totale(righe, profondita.z_crit_utilizzato_m)
    data = EdometricoOutput(carico=carico, profondita_critica=profondita, righe=righe, cedimento=cedimento)
    return success(data, inputs)


TOOLS = (
    Tool(
        name="geo-cedimento-edometrico",
        title="Cedimento edometrico di una fondazione rettangolare su terreno stratificato",
        group="Geotecnica / Cedimenti",
        norm="NTC2018 §6.2.2 / Circolare 2019 C6.2.2 (metodo edometrico di Terzaghi)",
        input_model=EdometricoInput,
        output_model=EdometricoOutput,
        run=run,
        example=ESEMPIO,
    ),
)

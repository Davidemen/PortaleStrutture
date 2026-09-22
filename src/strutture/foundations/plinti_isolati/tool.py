"""Tool registration: `fond-plinto-isolato` — one composed tool verifying one isolated-footing type
against a table of support reactions (docs/architecture-batch2.md §1 `foundations/plinti_isolati`)."""
import logging

from strutture.shared.report import Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tool import Tool

from .calcolo import calcola
from .capacita_portante import AVVISO_BLOCCO_IGNORATO_LEGACY, AVVISO_SISMICO
from .capacita_portante_checks import checks_capacita_portante
from .checks_inviluppo import checks_inviluppo
from .input import PlintoIsolatoInput
from .models import PlintoIsolatoOutput
from .relazione import relazione
from .schizzo import disegna as disegna_schizzo
from .sle_checks import sle_checks

logger = logging.getLogger(__name__)

ESEMPIO = {
    "ax_m": 4.0, "by_m": 4.0, "h_plinto_m": 0.8, "h_interro_m": 4.5,
    "gamma_terreno_kNm3": 20.0, "phi_terreno_deg": 30.0,
    "classe_calcestruzzo": "C35/45", "grado_acciaio": "B500C", "gamma_s": 1.15,
    "copriferro_cm": 8.0, "passo_armatura_cm": 12.2, "diametro_manuale_x_mm": 20.0, "diametro_manuale_y_mm": 20.0,
    "resistenze": [
        {"famiglia": "SLU_STR", "sigma_ammissibile": 2.0}, {"famiglia": "SLU_EQU", "sigma_ammissibile": 2.0},
        {"famiglia": "SLV_STR", "sigma_ammissibile": 2.0}, {"famiglia": "SLV_EQU", "sigma_ammissibile": 2.0},
        {"famiglia": "SLE_RARA", "sigma_ammissibile": 1.5}, {"famiglia": "SLE_FREQ", "sigma_ammissibile": 1.5},
        {"famiglia": "SLE_QP", "sigma_ammissibile": 1.5},
    ],
    "sistema_unita": "tecnico",
    "reazioni": [
        {"nodo": 1832, "combo": "ULS1", "famiglia": "SLU_STR", "fx_kN": 0.131665, "fy_kN": 5.37205,
         "fz_kN": 220.927, "mx_kNm": -36.4022, "my_kNm": 1.31727, "mz_kNm": -0.0608972},
    ],
}


def run(inputs: PlintoIsolatoInput) -> Report[PlintoIsolatoOutput]:
    """Compose the per-row verification, the family envelopes and the reinforcement/SLS design."""
    c = calcola(inputs)

    checks = (
        *checks_inviluppo(c.inviluppo_righe, inputs.resistenze, sistema_unita=inputs.sistema_unita,
                           legacy_compat=inputs.legacy_compat),
        *sle_checks(c.sle_result, c.materiali_result.calcestruzzo.fck_MPa, c.materiali_result.acciaio.fyk_MPa),
        *checks_capacita_portante(c.capacita_portante_result),
    )

    mu_ribaltamento_candidati = [
        v for v in (_minimo(c.inviluppo_righe, "ribaltamento_x_min"), _minimo(c.inviluppo_righe, "ribaltamento_y_min"))
        if v is not None
    ]
    schizzo: Sketch | None
    try:
        schizzo = disegna_schizzo(inputs, c.riga_governante)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per fond-plinto-isolato")
        schizzo = None
    data = PlintoIsolatoOutput(
        materiali=c.materiali_result, righe=c.righe, inviluppo=c.inviluppo_righe, eccentricita=c.eccentricita,
        governante=c.riga_governante, flessione=c.flessione_result, sle=c.sle_result,
        capacita_portante=c.capacita_portante_result,
        sigma_max_governante_kpa=c.riga_governante.sigma_max_kpa,
        mu_scorrimento_minimo=_minimo(c.inviluppo_righe, "scorrimento_min"),
        mu_ribaltamento_minimo=min(mu_ribaltamento_candidati) if mu_ribaltamento_candidati else None,
        schizzo=schizzo,
    )
    return success(
        data, inputs, checks=checks, warnings=c.avvisi_capacita_portante,
        avvisi_campi={AVVISO_BLOCCO_IGNORATO_LEGACY: "legacy_compat", AVVISO_SISMICO: "terreno_condizione"},
    )


def _minimo(inviluppo_righe: tuple, grandezza: str) -> float | None:
    valori = [r.valore for r in inviluppo_righe if r.grandezza == grandezza]
    return min(valori) if valori else None


TOOLS = (
    Tool(
        name="fond-plinto-isolato",
        title="Verifica plinto isolato su tabella reazioni",
        group="Fondazioni / Plinti",
        norm="NTC2018 §6.4.2 / §6.4.3, EC2 §7.2/§7.3",
        input_model=PlintoIsolatoInput,
        output_model=PlintoIsolatoOutput,
        run=run,
        example=ESEMPIO,
        summary="Verifica portanza, scorrimento, ribaltamento e armatura di un plinto isolato su tutte le combinazioni di carico.",
        live=False,
        relazione=relazione,
    ),
)

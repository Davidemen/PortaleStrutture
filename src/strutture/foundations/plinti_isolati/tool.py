"""Tool registration: `fond-plinto-isolato` — one composed tool verifying one isolated-footing type
against a table of support reactions (docs/architecture-batch2.md §1 `foundations/plinti_isolati`)."""
import logging

from strutture.shared.load_table import governing
from strutture.shared.report import Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tool import Tool

from .capacita_portante import capacita_portante
from .capacita_portante_checks import checks_capacita_portante
from .checks_inviluppo import checks_inviluppo
from .flessione import flessione
from .input import PlintoIsolatoInput
from .inviluppo import eccentricita_globale, inviluppo
from .materiali import materiali
from .models import PlintoIsolatoOutput
from .riga_verifica import RigaVerifica, riga_verifica
from .schizzo import disegna as disegna_schizzo
from .sle import sle, sle_checks

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
    righe: tuple[RigaVerifica, ...] = tuple(
        riga_verifica(
            row, inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.h_interro_m,
            inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.h_pedestal_sopra_m, inputs.h_pedestal_sotto_m,
            inputs.offset_leva_m, inputs.ex_m, inputs.ey_m, inputs.gamma_terreno_kNm3, inputs.phi_terreno_deg,
            metodo_pressioni=inputs.metodo_pressioni, legacy_compat=inputs.legacy_compat,
        )
        for row in inputs.reazioni
    )
    inviluppo_righe = inviluppo(righe)
    eccentricita = eccentricita_globale(righe)
    materiali_result = materiali(inputs.classe_calcestruzzo, inputs.grado_acciaio, inputs.gamma_s,
                                  legacy_compat=inputs.legacy_compat)
    flessione_result = flessione(
        inviluppo_righe, inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.a_pedestal_m, inputs.b_pedestal_m,
        inputs.ex_m, inputs.ey_m, inputs.copriferro_cm, inputs.passo_armatura_cm,
        inputs.diametro_manuale_x_mm, inputs.diametro_manuale_y_mm,
        materiali_result.acciaio.fyd_MPa, materiali_result.acciaio.fyk_MPa, materiali_result.calcestruzzo.fctm_MPa,
        legacy_compat=inputs.legacy_compat,
    )
    sle_result = sle(inviluppo_righe, flessione_result, inputs.ax_m, inputs.by_m, inputs.h_plinto_m,
                      inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.ex_m, inputs.ey_m,
                      copriferro_cm=inputs.copriferro_cm, legacy_compat=inputs.legacy_compat)
    capacita_portante_result, avvisi_capacita_portante = capacita_portante(righe, inputs)

    governante = governing(righe, lambda r: r.sigma_max_kpa, "max")  # type: ignore[arg-type]
    if governante is None:
        raise ValueError("la tabella reazioni non puo' essere vuota")
    riga_governante = righe[governante.indice]

    checks = (
        *checks_inviluppo(inviluppo_righe, inputs.resistenze, sistema_unita=inputs.sistema_unita,
                           legacy_compat=inputs.legacy_compat),
        *sle_checks(sle_result, materiali_result.calcestruzzo.fck_MPa, materiali_result.acciaio.fyk_MPa),
        *checks_capacita_portante(capacita_portante_result),
    )

    mu_ribaltamento_candidati = [
        v for v in (_minimo(inviluppo_righe, "ribaltamento_x_min"), _minimo(inviluppo_righe, "ribaltamento_y_min"))
        if v is not None
    ]
    schizzo: Sketch | None
    try:
        schizzo = disegna_schizzo(inputs, riga_governante)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per fond-plinto-isolato")
        schizzo = None
    data = PlintoIsolatoOutput(
        materiali=materiali_result, righe=righe, inviluppo=inviluppo_righe, eccentricita=eccentricita,
        governante=riga_governante, flessione=flessione_result, sle=sle_result,
        capacita_portante=capacita_portante_result,
        sigma_max_governante_kpa=riga_governante.sigma_max_kpa,
        mu_scorrimento_minimo=_minimo(inviluppo_righe, "scorrimento_min"),
        mu_ribaltamento_minimo=min(mu_ribaltamento_candidati) if mu_ribaltamento_candidati else None,
        schizzo=schizzo,
    )
    return success(data, inputs, checks=checks, warnings=avvisi_capacita_portante)


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
    ),
)

"""Tool registration: `muro-sostegno` (cantilever retaining wall, per metre run).

One composed Tool per docs/BUILD_CONTRACT.md "Member tools": `run_muro_sostegno` composes the
small step modules (geometria, parametri_sismici, angoli_progetto, coulomb/mononobe_okabe,
ribaltamento_scorrimento, pressioni_terreno, capacita_portante_fondazione (facoltativo),
armatura_paramento, armatura_fondazione_valle, armatura_fondazione_monte) for all 8 combinations
(STR_1, STR_2, GEO_1, GEO_2, EQU_1, EQU_2, SISMA_1, SISMA_2) and returns every intermediate group.

Per combination assembly lives in the sibling `*_combo.py`/`verifica_*.py`/`combo_*.py` modules
(regola dura 12, moduli di calcolo <= 150 righe); this module stays the entry point (regola dura
15) and re-exports the names other modules/tests already import from it.
"""
import logging

from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.report import Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tool import Tool

from .armatura_comune import check_armatura_minima
from .avvisi_muro import avvisi_scorrimento, campi_degli_avvisi
from .capacita_portante_muro import (
    AVVISO_CAPACITA_PORTANTE,
    AVVISO_CAPACITA_PORTANTE_SISMICA,
    AVVISO_ECCENTRICITA_LIMITE,
    AVVISO_TERRENO_IGNORATO_LEGACY,
    esito_capacita_portante,
)
from .combinazioni import ALL_COMBOS
from .combo_armatura_fondazione_monte import run_armatura_fondazione_monte
from .combo_armatura_fondazione_valle import run_armatura_fondazione_valle
from .combo_armatura_paramento import run_armatura_paramento
from .geometria import geometria_muro
from .models import MuroSostegnoInput, MuroSostegnoOutput
from .parametri_sismici import parametri_sismici
from .pressioni_combo import pressioni_combo
from .relazione import relazione as relazione_muro_sostegno
from .schizzo import disegna as disegna_schizzo
from .spinta_combo import spinta_combo
from .verifica_ribaltamento_scorrimento import ribaltamento_scorrimento_combo

logger = logging.getLogger(__name__)

__all__ = [
    "AVVISO_CAPACITA_PORTANTE",
    "AVVISO_CAPACITA_PORTANTE_SISMICA",
    "AVVISO_ECCENTRICITA_LIMITE",
    "AVVISO_TERRENO_IGNORATO_LEGACY",
    "ESEMPIO_TRATTO_A",
    "TOOLS",
    "run_muro_sostegno",
]

# docs/specs/muro-sostegno.md §"Golden test case" (Tratto A, cached against the original sheet).
ESEMPIO_TRATTO_A = {
    "gamma_terr_sat_kN_m3": 19.7, "gamma_terr_secco_kN_m3": 15.6, "phi_deg": 30.69, "delta_deg": 0,
    "beta_deg": 0, "psi_deg": 90, "omega_deg": 0, "ag_g": 0.136, "f0": 2.419,
    "categoria_sottosuolo": "C", "categoria_topografica": "T1", "beta_m": 0.24, "gamma_e": 1.0,
    "gamma_cls_kN_m3": 25, "s_base_m": 0.49, "s_top_m": 0.25, "s_fond_m": 0.3, "h_muro_m": 2.4,
    "b_valle_m": 0.26, "b_monte_m": 1.15, "q_kN_m2": 2, "copertura_paramento_m": 0.06,
    "grado_acciaio": "B450C", "passo_arm_paramento_m": 0.2, "copertura_fondazione_m": 0.06,
    "passo_arm_fondazione_m": 0.2,
}


def _disegna_schizzo_sicuro(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno) -> Sketch | None:
    try:
        return disegna_schizzo(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per muro-sostegno")
        return None


def _calcola_gruppi(inputs: MuroSostegnoInput):
    """Geometria/sismici + le tre serie per combinazione (spinte, ribaltamento/scorrimento,
    pressioni), condivise da tutti i gruppi a valle (armature, capacità portante, schizzo)."""
    geometria = geometria_muro(
        h_muro_m=inputs.h_muro_m, s_fond_m=inputs.s_fond_m, s_base_m=inputs.s_base_m, s_top_m=inputs.s_top_m, b_valle_m=inputs.b_valle_m, b_monte_m=inputs.b_monte_m
    )
    sismici = parametri_sismici(inputs.categoria_sottosuolo, inputs.categoria_topografica, inputs.f0, inputs.ag_g)
    spinte = tuple(spinta_combo(nome, inputs=inputs, geometria=geometria, s_sismico=sismici.s) for nome in ALL_COMBOS)
    ribaltamento_scorrimento = tuple(ribaltamento_scorrimento_combo(spinta, inputs=inputs, geometria=geometria) for spinta in spinte)
    pressioni_terreno = tuple(
        pressioni_combo(spinta, verifica, geometria=geometria) for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True)
    )
    return geometria, sismici, spinte, ribaltamento_scorrimento, pressioni_terreno


def run_muro_sostegno(inputs: MuroSostegnoInput) -> Report[MuroSostegnoOutput]:
    geometria, sismici, spinte, ribaltamento_scorrimento, pressioni_terreno = _calcola_gruppi(inputs)

    fyd_MPa = rebar_properties(inputs.grado_acciaio).fyd_MPa
    armatura_paramento = run_armatura_paramento(spinte, ribaltamento_scorrimento, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
    armatura_fondazione_valle = run_armatura_fondazione_valle(spinte, pressioni_terreno, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
    armatura_fondazione_monte = run_armatura_fondazione_monte(
        spinte, ribaltamento_scorrimento, pressioni_terreno, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa
    )
    capacita_portante_fondazione, capacita_portante_checks, warnings = esito_capacita_portante(
        spinte, ribaltamento_scorrimento, pressioni_terreno, inputs=inputs, geometria=geometria
    )
    schizzo = _disegna_schizzo_sicuro(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno)

    data = MuroSostegnoOutput(
        geometria=geometria,
        parametri_sismici=sismici,
        spinte=spinte,
        ribaltamento_scorrimento=ribaltamento_scorrimento,
        pressioni_terreno=pressioni_terreno,
        capacita_portante_fondazione=capacita_portante_fondazione,
        armatura_paramento=armatura_paramento,
        armatura_fondazione_valle=armatura_fondazione_valle,
        armatura_fondazione_monte=armatura_fondazione_monte,
        schizzo=schizzo,
    )
    checks = (
        tuple(c for v in ribaltamento_scorrimento for c in (v.verifica_ribaltamento, v.verifica_scorrimento))
        + capacita_portante_checks
        + (
            check_armatura_minima("Armatura minima paramento", armatura_paramento),
            check_armatura_minima("Armatura minima mancia", armatura_fondazione_valle),
            check_armatura_minima("Armatura minima tacco", armatura_fondazione_monte),
        )
    )
    tutti_gli_avvisi = warnings + avvisi_scorrimento(inputs)
    return success(data, inputs, checks=checks, warnings=tutti_gli_avvisi, avvisi_campi=campi_degli_avvisi(tutti_gli_avvisi))


TOOLS = (
    Tool(
        name="muro-sostegno",
        title="Muro di sostegno a mensola",
        group="Geotecnica / Muri di sostegno",
        norm="NTC2018 §6.5.3.1.1, §6.5.3.1.2, §6.4.2.1, §7.11.6.2.1, §4.1.2",
        input_model=MuroSostegnoInput,
        output_model=MuroSostegnoOutput,
        run=run_muro_sostegno,
        example=ESEMPIO_TRATTO_A,
        summary="Verifica un muro di sostegno a mensola a ribaltamento, scorrimento, pressione sul terreno, capacità portante (facoltativa) e armatura, per le 8 combinazioni di carico statiche e sismiche.",
        relazione=relazione_muro_sostegno,
    ),
)

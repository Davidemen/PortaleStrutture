"""Composed tool: `geo-cedimento-elastico-timoshenko-goodier` (`docs/specs/geo-cedimenti-elastico.md`
Tool 2), based on the only complete draft, `Elastico_Timoshenko_Goodier_3` (μ=0.35); the earlier
`Elastico_Timoshenko_Goodier` (μ=0.2) and `_2` (μ=0.25) sheets are dead drafts (their per-layer IF
column is never filled in) and are not ported."""
import logging

from strutture.shared.report import CalcError, Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tables import KeyNotFound
from strutture.shared.tool import Tool

from .boundary import to_kpa, to_m
from .ground_to_base import shift_to_base
from .models_tg import CedimentoTG, FattoriTG, GeometriaTG, ModuloTG, TimoshenkoGoodierInput, TimoshenkoGoodierOutput
from .relazione_timoshenko_goodier import relazione_timoshenko_goodier
from .schizzo import disegna_timoshenko_goodier
from .settlement_tg import deltah_bordo_mm, deltah_centro_mm
from .steinbrenner_factors import aspect_ratio, depth_ratio_bordo, depth_ratio_centro, influence_factors
from .weighted_es import es_weighted_modulus

logger = logging.getLogger(__name__)

H_SIGNIFICATIVO_DEFAULT_FACTOR = 5.0  # "C7={=+C4*5}": significant depth defaults to 5·B

ESEMPIO = {
    "sistema_unita": "SI", "b": 1.0, "l": 1.0, "d": 0.5, "mu": 0.35, "q": 90.2212,
    "strati": [{"z_top_m": 0.0, "z_bot_m": 2.10, "modulo_MPa": 17.652}, {"z_top_m": 2.10, "z_bot_m": 120.0, "modulo_MPa": 27.4586}],
    "if_centro": 0.65, "if_bordo": 0.78,
}


def run_timoshenko_goodier(inputs: TimoshenkoGoodierInput) -> Report[TimoshenkoGoodierOutput]:
    sistema = inputs.sistema_unita
    q_kPa = to_kpa(inputs.q, sistema)
    b_m, l_m, d_m = to_m(inputs.b, sistema), to_m(inputs.l, sistema), to_m(inputs.d, sistema)
    h_m = to_m(inputs.h_significativo, sistema) if inputs.h_significativo is not None else H_SIGNIFICATIVO_DEFAULT_FACTOR * b_m

    layers = shift_to_base(inputs.strati, d_m)
    try:
        es_MPa = es_weighted_modulus(layers, h_m, legacy_compat=inputs.legacy_compat)
    except KeyNotFound as error:
        raise CalcError(str(error)) from error

    a = aspect_ratio(b_m, l_m)
    b_centro, b_bordo = depth_ratio_centro(h_m, b_m), depth_ratio_bordo(h_m, b_m)
    is_centro, is_bordo = influence_factors(a, b_centro, b_bordo, inputs.mu, legacy_compat=inputs.legacy_compat)

    schizzo: Sketch | None
    try:
        schizzo = disegna_timoshenko_goodier(inputs)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per geo-cedimento-elastico-timoshenko-goodier")
        schizzo = None

    data = TimoshenkoGoodierOutput(
        geometria=GeometriaTG(a=a, b_centro=b_centro, b_bordo=b_bordo),
        modulo=ModuloTG(es_MPa=es_MPa),
        fattori=FattoriTG(is_centro=is_centro, is_bordo=is_bordo, if_centro=inputs.if_centro, if_bordo=inputs.if_bordo),
        cedimento=CedimentoTG(
            delta_h_centro_mm=deltah_centro_mm(q_kPa, b_m, inputs.mu, es_MPa, is_centro, inputs.if_centro, legacy_compat=inputs.legacy_compat),
            delta_h_bordo_mm=deltah_bordo_mm(q_kPa, b_m, inputs.mu, es_MPa, is_bordo, inputs.if_bordo, legacy_compat=inputs.legacy_compat),
        ),
        schizzo=schizzo,
    )
    return success(data, inputs)


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="geo-cedimento-elastico-timoshenko-goodier",
        title="Cedimento elastico - Timoshenko & Goodier (rettangolo flessibile)",
        group="Geotecnica / Cedimenti",
        norm="Timoshenko & Goodier 1970 (?)",
        input_model=TimoshenkoGoodierInput,
        output_model=TimoshenkoGoodierOutput,
        run=run_timoshenko_goodier,
        example=ESEMPIO,
        summary="Calcola il cedimento elastico immediato di una fondazione flessibile con il metodo di Timoshenko e Goodier, al centro e al bordo.",
        relazione=relazione_timoshenko_goodier,
    ),
)

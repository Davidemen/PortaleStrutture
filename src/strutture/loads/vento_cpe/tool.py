"""Tool registration: vento-cpe-rettangolare. Circ. NTC2019 §C3.3.8.1."""
import logging

from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .classification import classify
from .cpe_leeward import cpe_leeward
from .cpe_side import cpe_side
from .cpe_windward import cpe_windward
from .hd_ratio import hd_ratio
from .models import DirectionResult, VentoCpeInput, VentoCpeOutput
from .schizzo import disegna as disegna_schizzo

logger = logging.getLogger(__name__)


def _direction(h: float, d: float) -> DirectionResult:
    hd = hd_ratio(h, d)
    return DirectionResult(
        h_d=hd,
        cpe_windward=cpe_windward(hd),
        cpe_side=cpe_side(hd),
        cpe_leeward=cpe_leeward(hd),
    )


def run(inputs: VentoCpeInput) -> Report[VentoCpeOutput]:
    dir1 = _direction(inputs.h, inputs.d)
    dir2 = _direction(inputs.h, inputs.b)  # sheet E6/E7 auto-swap b,d for direction 2

    try:
        schizzo = disegna_schizzo(inputs, dir1, dir2)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per vento-cpe-rettangolare")
        schizzo = None

    classification = classify(dir1.h_d, dir2.h_d, legacy_compat=inputs.legacy_compat)
    data = VentoCpeOutput(classification=classification, dir1=dir1, dir2=dir2, schizzo=schizzo)
    return success(data, inputs)


TOOLS = (
    Tool(
        name="vento-cpe-rettangolare",
        title="Coefficienti Cpe vento — edifici a pianta rettangolare",
        group="Carichi / Vento",
        norm="Circ. NTC2019 §C3.3.8.1",
        input_model=VentoCpeInput,
        output_model=VentoCpeOutput,
        run=run,
        example={"b": 15, "d": 12, "h": 9},
        summary="Calcola i coefficienti di pressione esterna del vento su un edificio a pianta rettangolare per entrambe le direzioni.",
    ),
)

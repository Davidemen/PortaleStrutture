"""Step (spec §4.5-6): return-period correction, NTC2018 eq. 3.3.2/3.3.3, Vento!H14/H15."""
import math

from strutture.shared.divergences import legacy

from .costanti import REFERENCE_RETURN_PERIOD_YEARS


def _fattore_gumbel(tr_anni: float) -> float:
    return 1 - 0.2 * math.log(-math.log(1 - 1 / tr_anni))


def coefficiente_periodo_ritorno(tr_anni: float) -> float:
    """cr(TR) = 0.75*sqrt(1-0.2*ln(-ln(1-1/TR))) (Vento!H14, NTC2018 eq. 3.3.3)."""
    return 0.75 * math.sqrt(_fattore_gumbel(tr_anni))


def velocita_riferimento(vref: float, tr_anni: float, legacy_compat: bool) -> float:
    """vr [m/s] (Vento!H15).

    legacy_compat=True riproduce la rinormalizzazione storica del foglio rispetto a TR=50
    (vr = vref*sqrt(fattore_gumbel(TR)/fattore_gumbel(50))), non prevista dalla norma: introduce
    un'inconsistenza con l'aR esposto (Vento!H14 = cr(TR), invariato), cioè aR*vref != vr — bug
    noto del foglio, riprodotto intenzionalmente (vedi docs/divergences/vento.md).
    legacy_compat=False applica `vr = vref*cr(TR)` (NTC2018 eq. 3.3.2/3.3.3), senza rinormalizzazione:
    qui aR*vref == vr sempre, per costruzione.
    """
    if legacy("vento/velocita-riferimento-rinormalizzata-su-tr50", legacy_compat):
        return vref * math.sqrt(_fattore_gumbel(tr_anni) / _fattore_gumbel(REFERENCE_RETURN_PERIOD_YEARS))
    return vref * coefficiente_periodo_ritorno(tr_anni)

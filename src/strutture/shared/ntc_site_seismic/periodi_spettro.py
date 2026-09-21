"""NTC 2018 §3.2.3.2.1 — corner periods TB, TC, TD of the horizontal response spectrum (Sisma!I48:I50)."""
from .models import PeriodiSpettroResult

TD_COSTANTE_S = 1.6  # NTC2018 §3.2.3.2.1: TD = 4·ag/g + 1.6


def periodi_spettro(cc: float, tc_star_s: float, ag_g: float) -> PeriodiSpettroResult:
    """TB, TC, TD (Sisma!I48/I49/I50)."""
    tc = cc * tc_star_s
    tb = tc / 3.0
    td = 4.0 * ag_g + TD_COSTANTE_S
    return PeriodiSpettroResult(tb=tb, tc=tc, td=td)

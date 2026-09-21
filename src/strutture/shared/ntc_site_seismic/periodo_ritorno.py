"""NTC 2018 §3.2.1 eq. 3.2.1 — periodo di ritorno TR = -VR/ln(1-PVR) (Sisma!D13:D16)."""
import math

from strutture.shared.tables import exact_lookup

from .models import PeriodiRitornoResult, StatoLimite
from .tables import PROBABILITA_SUPERAMENTO_PVR


def periodo_ritorno(vr_anni: float, stato_limite: StatoLimite) -> float:
    """TR for one limit state, rounded to the nearest year (Sisma!D13/D14/D15/D16 `=ROUND(...,0)`)."""
    pvr = exact_lookup(PROBABILITA_SUPERAMENTO_PVR, stato_limite)
    return round(-vr_anni / math.log(1 - pvr))


def periodi_ritorno(vr_anni: float) -> PeriodiRitornoResult:
    """TR for all four limit states at once (Sisma!D13:D16)."""
    return PeriodiRitornoResult(
        slo=periodo_ritorno(vr_anni, "SLO"),
        sld=periodo_ritorno(vr_anni, "SLD"),
        slv=periodo_ritorno(vr_anni, "SLV"),
        slc=periodo_ritorno(vr_anni, "SLC"),
    )

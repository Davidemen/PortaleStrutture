"""NTC 2018 §2.4.3 eq. 3.2.0 — vita di riferimento VR = VN·Cu, with the code's 35-year floor."""
from strutture.shared.divergences import legacy

from .models import VitaRiferimentoResult

VITA_RIFERIMENTO_MINIMA_ANNI = 35.0  # NTC2018 §2.4.3: VR non può essere inferiore a 35 anni.


def vita_riferimento(vn_anni: float, cu: float, *, legacy_compat: bool = False) -> VitaRiferimentoResult:
    """VR (Sisma!I10 = I9*I7). `legacy_compat=True` reproduces the sheet, which omits the 35-year floor."""
    vr = vn_anni * cu
    if not legacy("ntc-site-seismic/vita-riferimento-senza-minimo-35-anni", legacy_compat):
        vr = max(vr, VITA_RIFERIMENTO_MINIMA_ANNI)
    return VitaRiferimentoResult(cu=cu, vr=vr)

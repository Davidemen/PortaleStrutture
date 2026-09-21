"""NTC 2018 §7.3.1 — riduzione del fattore di struttura per irregolarità in altezza (Sisma!I40)."""
from typing import Final

KR_REGOLARE: Final[float] = 1.0
KR_NON_REGOLARE: Final[float] = 0.8


def kr_regolare_altezza(regolare_altezza: str) -> float:
    """KR: 1.0 se la struttura è regolare in altezza ("SI"), 0.8 altrimenti ("NO").

    Compared case-insensitively for the same reason as `stato_limite.is_stato_limite_uls`
    (Sisma!I41 compares the uppercase dropdown against the lowercase literal "si")."""
    return KR_REGOLARE if regolare_altezza.strip().upper() == "SI" else KR_NON_REGOLARE

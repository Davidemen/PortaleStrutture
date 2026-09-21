"""EN1993-1-1 §3.2.6 — costanti elastiche dell'acciaio strutturale."""
from .tables import E_MPA, POISSON_RATIO


def modulo_taglio(e_MPa: float = E_MPA, *, poisson: float = POISSON_RATIO) -> float:
    """G = E/(2*(1+ν)), MPa."""
    return e_MPa / (2.0 * (1.0 + poisson))

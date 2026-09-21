"""NTC 2018 §3.2.3.2.1 eq. 3.2.6 — damping correction factor η (Sisma!I38)."""
import math
from typing import Final

ETA_MIN: Final[float] = 0.55  # NTC2018 eq. 3.2.6: eta = sqrt(10/(5+xi)) >= 0.55


def smorzamento_eta(xi_pct: float) -> float:
    """η = max(sqrt(10/(5+ξ)), 0.55), ξ = smorzamento viscoso equivalente in %."""
    return max(math.sqrt(10.0 / (5.0 + xi_pct)), ETA_MIN)

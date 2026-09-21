"""U/(V·(1+√(W/X))²) branch shared by the Coulomb (static) and Mononobe-Okabe (seismic) active-thrust
coefficients (NTC2018 §6.5.3.1.1 / §7.11.6.2.1, muro-sostegno rows 56/87)."""
import math


def rapporto_spinta(u: float, v: float, w: float, x: float, *, cuneo_valido: bool) -> float:
    """`cuneo_valido` is the sheet's `IF(β ≤ ..., ...)` branch test (wedge geometry admissible)."""
    if cuneo_valido:
        return u / (v * (1 + math.sqrt(w / x)) ** 2)
    return u / v

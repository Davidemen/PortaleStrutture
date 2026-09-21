"""Crack-width amplitude and its utilisation ratio for `ca-apertura-fessure`, Circ. 2019
§C4.1.5, calc step 12 (`Apertura delle fessure!E47/D48`)."""
import math

FATTORE_AMPIEZZA_FESSURA = 1.7  # Circ. 2019 §C4.1.5 — wk = 1.7*εsm*Δsm,eff [E47]


def apertura_fessure_wk_mm(fattore_ampiezza: float, epsilon_sm: float, delta_sm_mm: float) -> float:
    """wk = fattore_ampiezza * εsm * Δsm,eff [E47], Circ. 2019 §C4.1.5."""
    return fattore_ampiezza * epsilon_sm * delta_sm_mm


def utilizzo_apertura_fessure(wk_mm: float, wlim_mm: float) -> float:
    """Tasso di sfruttamento wk/wlim, arrotondato per eccesso a 2 decimali [D48]."""
    if wlim_mm <= 0:
        raise ValueError(f"wlim_mm deve essere positivo, ricevuto {wlim_mm}")
    return math.ceil(wk_mm / wlim_mm * 100) / 100

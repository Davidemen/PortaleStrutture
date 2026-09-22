"""Minimum flexural reinforcement of the wall's three cantilevers (stem, toe, heel), per metre of
wall: NTC2018 §4.1.6.1.1 / EN 1992-1-1 §9.2.1.1 eq. (9.1N), A_s,min = max(0,26·f_ctm/f_yk; 0,0013)·b·d
with b = 1 m. The spreadsheet sized the bars on the flexural requirement alone (no minimum at
all): the engineering proof-read of the calculation report found the stem asking for 1,55 cm²/m
against a code minimum of ≈6,4 cm²/m. `legacy_compat=True` keeps the sheet's choice (register:
muro-sostegno/armatura-senza-minimo-normativo); the check itself is reported in both modes."""
import math

from strutture.shared.divergences import legacy

LARGHEZZA_STRISCIA_MM = 1000.0
RAPPORTO_FCTM_FYK = 0.26  # EN 1992-1-1 eq. (9.1N)
RAPPORTO_MINIMO_ASSOLUTO = 0.0013
MM2_PER_CM2 = 100.0
M_PER_MM = 1000.0


def as_min_cm2_m(*, fctm_MPa: float, fyk_MPa: float, d_m: float) -> float:
    """A_s,min [cm²/m] = max(0,26·f_ctm/f_yk; 0,0013)·b·d, b = 1 m."""
    d_mm = d_m * M_PER_MM
    rapporto = max(RAPPORTO_FCTM_FYK * fctm_MPa / fyk_MPa, RAPPORTO_MINIMO_ASSOLUTO)
    return rapporto * LARGHEZZA_STRISCIA_MM * d_mm / MM2_PER_CM2


def as_progetto_cm2_m(as_nec_cm2_m: float, as_min_cm2_m_: float, *, legacy_compat: bool) -> float:
    """The area the bars are chosen for: max(A_s,nec; A_s,min) — the sheet used A_s,nec alone."""
    if legacy("muro-sostegno/armatura-senza-minimo-normativo", legacy_compat):
        return as_nec_cm2_m
    return max(as_nec_cm2_m, as_min_cm2_m_)


def area_disposta_cm2_m(*, diametro_mm: float, passo_m: float) -> float:
    """Area per metre of one bar layer φ/s: π·φ²/4 per bar, 1/s bars per metre."""
    return math.pi * diametro_mm**2 / 4.0 / passo_m / MM2_PER_CM2

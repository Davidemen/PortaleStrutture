"""Elastic critical loads (column-check!Y21, Y22, AV38 — EN1993-1-1 §6.3.1.2/6.3.1.4)."""
import math

from strutture.shared.units import n_to_kn


def ncr_flessionale_kN(e_MPa: float, inerzia_mm4: float, lcr_mm: float) -> float:
    """column-check!Y21/Y22 — Ncr = pi^2*E*I/Lcr^2."""
    return n_to_kn(math.pi**2 * e_MPa * inerzia_mm4 / lcr_mm**2)


def ncr_torsionale_kN(
    g_MPa: float, it_mm4: float, e_MPa: float, iw_mm6: float, lt_mm: float, i0_quadro_mm2: float
) -> float:
    """column-check!AV38 — Ncr,T = (1/i0^2)*(G*IT + pi^2*E*Iw/lT^2)."""
    return n_to_kn((1.0 / i0_quadro_mm2) * (g_MPa * it_mm4 + math.pi**2 * e_MPa * iw_mm6 / lt_mm**2))

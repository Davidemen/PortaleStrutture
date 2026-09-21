"""Geometria utile della sezione: altezza utile d e braccio di leva interno z.

NTC2018 §4.1.2.3.4.2 (d, altezza utile) e EC2 §6.2.3 (z ≈ 0.9·d, braccio di leva a taglio,
usato anche dal foglio come riferimento per i limiti di armatura, vedi divergenze).
"""
from strutture.shared.report import CalcError

LEVA_INTERNA_FATTORE = 0.9  # EC2 §6.2.3 — approssimazione usuale del braccio di leva interno z=0.9d


def altezza_utile_mm(h_mm: float, copriferro_mm: float) -> float:
    """d = H - c, altezza utile della sezione [mm]."""
    d_mm = h_mm - copriferro_mm
    if d_mm <= 0:
        raise CalcError(f"copriferro {copriferro_mm} mm >= altezza {h_mm} mm: altezza utile non positiva")
    return d_mm


def braccio_leva_mm(d_mm: float) -> float:
    """z = 0.9*d, braccio di leva interno [mm]."""
    return LEVA_INTERNA_FATTORE * d_mm

"""Step: pure-compression check (no steel term), row G27/K27/H26."""
from strutture.shared.units import n_to_kn


def compressione_nrcd_kN(ac_mm2: float, fcd_MPa: float) -> float:
    """H26: NRcd = Ac*fcd (concrete-only capacity)."""
    return n_to_kn(ac_mm2 * fcd_MPa)


def verifica_compressione(nrcd_kN: float, ned_kN: float) -> bool:
    return nrcd_kN > ned_kN

"""Coulomb active earth-pressure coefficient Ka, static case (NTC2018 §6.5.3.1.1, muro-sostegno row 56)."""
import math

from .rapporto_spinta import rapporto_spinta


def ka_coulomb(*, phi_d_rad: float, delta_d_rad: float, beta_rad: float, psi_rad: float) -> float:
    u = math.sin(psi_rad + phi_d_rad) ** 2
    v = math.sin(psi_rad) ** 2 * math.sin(psi_rad - delta_d_rad)
    w = math.sin(phi_d_rad + delta_d_rad) * math.sin(phi_d_rad - beta_rad)
    x = math.sin(psi_rad - delta_d_rad) * math.sin(psi_rad + beta_rad)
    return rapporto_spinta(u, v, w, x, cuneo_valido=beta_rad <= phi_d_rad)

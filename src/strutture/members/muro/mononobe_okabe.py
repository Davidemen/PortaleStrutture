"""Mononobe-Okabe seismic active-thrust coefficient Kae and kh/kv/θ (NTC2018 §7.11.6.2.1 / EC8-5
Annex E, muro-sostegno rows 80-81/87-88)."""
import math
from typing import NamedTuple

from .rapporto_spinta import rapporto_spinta


class CoefficientiSismici(NamedTuple):
    kh: float
    kv: float
    theta_rad: float


def coefficienti_sismici(*, s: float, ag_g: float, beta_m: float, segno_kv: float) -> CoefficientiSismici:
    """kh = S·ag·βm; kv = segno_kv·0.5·kh (segno_kv = +1 for SISMA.1, -1 for SISMA.2); θ = atan(kh/(1+kv))."""
    kh = s * ag_g * beta_m
    kv = segno_kv * 0.5 * kh
    return CoefficientiSismici(kh=kh, kv=kv, theta_rad=math.atan(kh / (1 + kv)))


def kae_mononobe_okabe(*, phi_d_rad: float, delta_d_rad: float, beta_rad: float, psi_rad: float, theta_rad: float) -> float:
    u = math.sin(psi_rad + phi_d_rad - theta_rad) ** 2
    v = math.cos(theta_rad) * math.sin(psi_rad) ** 2 * math.sin(psi_rad - delta_d_rad - theta_rad)
    w = math.sin(phi_d_rad + delta_d_rad) * math.sin(phi_d_rad - beta_rad - theta_rad)
    x = math.sin(psi_rad - delta_d_rad - theta_rad) * math.sin(psi_rad + beta_rad)
    return rapporto_spinta(u, v, w, x, cuneo_valido=beta_rad <= (phi_d_rad - theta_rad))

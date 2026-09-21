"""EN 1992-1-1 §6.5.4(4) node design compressive stress limits: CCC (k1), CCT (k2), CTT (k3) times ν'*fcd.
EN default coefficients k1=1.0, k2=0.85, k3=0.75, exposed as keywords for national-annex overrides."""
from typing import Literal

from .models import NodeResistance
from .nu_prime import nu_prime

Node = Literal["CCC", "CCT", "CTT"]

K1_CCC_EN = 1.0
K2_CCT_EN = 0.85
K3_CTT_EN = 0.75


def sigma_rd_max(
    fck_MPa: float,
    nodo: Node,
    gamma_c: float = 1.5,
    *,
    alpha_cc: float = 1.0,
    k1: float = K1_CCC_EN,
    k2: float = K2_CCT_EN,
    k3: float = K3_CTT_EN,
) -> NodeResistance:
    """sigma_Rd,max = k_i * nu' * fcd, with k_i selected by node class (CCC->k1, CCT->k2, CTT->k3)."""
    if gamma_c <= 0:
        raise ValueError(f"gamma_c must be positive, got {gamma_c}")

    coefficients: dict[Node, float] = {"CCC": k1, "CCT": k2, "CTT": k3}
    if nodo not in coefficients:
        raise ValueError(f"unknown nodo {nodo!r}, expected 'CCC', 'CCT' or 'CTT'")

    nu = nu_prime(fck_MPa)
    fcd_MPa = alpha_cc * fck_MPa / gamma_c
    return NodeResistance(sigma_rd_max_MPa=coefficients[nodo] * nu * fcd_MPa, nu_prime=nu, fcd_MPa=fcd_MPa)

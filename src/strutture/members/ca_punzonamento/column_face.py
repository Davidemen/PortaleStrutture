"""Spec steps 2-4: verification at the column-face control perimeter u0. `v_rd_max` is the only
divergent formula (docs/specs/ca-punzonamento.md §7.4): the sheet uses an unrelated simplified
`0.2*0.85*fck/1.5` coefficient instead of EC2§6.4.5(3) `coeff_vrd_max*nu*fcd`
(`shared.ec2_shear.v_rd_max`) — `coeff_vrd_max` is the tool's own explicit, user-chosen advanced
input (0.4 EN 1992-1-1/A1:2014 default, or 0.5 EN 1992-1-1:2004 + Appendice Nazionale italiana; see
docs/divergences/ec2-shared.md)."""
import math

from strutture.shared.ec2_shear import v_rd_max
from strutture.shared.materials.concrete import ALPHA_CC

from .effective_depth import column_shape
from .models import FacciaPilastroOutput
from .perimeter_area import perimeter_length_mm

V_RD_MAX_LEGACY_COEFFICIENT = 0.2 * 0.85 / 1.5  # sheet D17, no EC2 basis (see module docstring)
GAMMA_C = 1.5  # EC2 Tab. 2.1N, persistent/transient design situations


def column_footprint_area_mm2(lato_a_mm: float, lato_b_mm: float, diametro_mm: float) -> float:
    """Column/pile cross-sectional area at the slab plane (sheet D15's own shape-aware IF branch)."""
    if column_shape(lato_a_mm) == "circ":
        return math.pi * (diametro_mm / 2.0) ** 2
    return lato_a_mm * lato_b_mm


def v_rd_max_MPa(fck_MPa: float, *, legacy_compat: bool, coeff_vrd_max: float) -> float:
    if legacy_compat:
        return V_RD_MAX_LEGACY_COEFFICIENT * fck_MPa
    return v_rd_max(fck_MPa, GAMMA_C, alpha_cc=ALPHA_CC, coefficient=coeff_vrd_max).v_rd_max_MPa


def faccia_pilastro(
    ved_kN: float, beta: float, pterreno_MPa: float, lato_a_mm: float, lato_b_mm: float,
    diametro_mm: float, u0_mm: float, d_mm: float, fck_MPa: float, *, legacy_compat: bool,
    coeff_vrd_max: float,
) -> FacciaPilastroOutput:
    area0_mm2 = column_footprint_area_mm2(lato_a_mm, lato_b_mm, diametro_mm)
    ved_red_0_kN = ved_kN * beta - pterreno_MPa * area0_mm2 / 1000.0
    v_ed_0 = ved_red_0_kN * 1000.0 / (u0_mm * d_mm)
    return FacciaPilastroOutput(
        v_rd_max_MPa=v_rd_max_MPa(fck_MPa, legacy_compat=legacy_compat, coeff_vrd_max=coeff_vrd_max),
        ved_red_0_kN=ved_red_0_kN,
        v_ed_0_MPa=v_ed_0,
    )


def u0_mm(lato_a_mm: float, lato_b_mm: float, diametro_mm: float) -> float:
    return perimeter_length_mm(lato_a_mm, lato_b_mm, diametro_mm, 0.0, None)

"""Spec steps 19-23: vertical shear-reinforcement ("cuciture") sizing (EC2§6.4.5(1)/§9.4.3(2), eq.
6.52/9.11). The stirrup grade has no sheet input, so it is fixed to B450C (`tables.STAFFA_GRADE`), the
current NTC2018 grade whose fyk=450 MPa matches the sheet's own baked-in Asw,min coefficient."""
import math

from strutture.shared.ec2_shear import fywd_ef as ec2_fywd_ef
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.rebar_catalog import bar_area

from .tables import STAFFA_GRADE

ASW_MIN_ALPHA_FACTOR = 1.5  # EC2 eq. 9.11 "1.5*sinα+cosα" for vertical links (α=90°)
VRD_CS1_ALPHA_FACTOR = 1.5  # same factor, in the single-stirrup resistance (EC2 eq. 6.52)
VRD_C_ENHANCEMENT_FRACTION = 0.75  # EC2 eq. 6.52 concrete-side fraction of vRd,c retained with reinforcement
FYWD_LEGACY_BASE_MPA = 250.0
FYWD_LEGACY_SLOPE = 0.25


def asw_min_mm2(fck_MPa: float, sr_mm: float, st_mm: float) -> float:
    fyk_MPa = rebar_properties(STAFFA_GRADE).fyk_MPa
    return 0.08 * fck_MPa**0.5 * sr_mm * st_mm / (fyk_MPa * ASW_MIN_ALPHA_FACTOR)


def v_rd_cs_min_kN(v_ed_i_MPa: float, v_rd_i_MPa: float, ui_mm: float, d_mm: float) -> float:
    """Required steel-side force at the governing perimeter (EC2 eq. 6.52 rearranged)."""
    return (v_ed_i_MPa - VRD_C_ENHANCEMENT_FRACTION * v_rd_i_MPa) * ui_mm * d_mm / 1000.0


def fywd_ef_MPa(d_mm: float, *, legacy_compat: bool) -> float:
    if legacy_compat:
        return FYWD_LEGACY_BASE_MPA + FYWD_LEGACY_SLOPE * d_mm
    fywd_MPa = rebar_properties(STAFFA_GRADE).fyd_MPa
    return ec2_fywd_ef(d_mm, fywd_MPa)


def v_rd_cs1_kN(d_mm: float, sr_mm: float, area_staffa_mm2: float, fywd_ef_MPa_: float) -> float:
    """Resistance of one stirrup summed around one radial perimeter (EC2 eq. 6.52)."""
    return VRD_CS1_ALPHA_FACTOR * (d_mm / sr_mm) * area_staffa_mm2 * fywd_ef_MPa_ / 1000.0


def n_f_richiesto(v_rd_cs_min_kN_: float, v_rd_cs1_kN_: float) -> int:
    """Excel CEILING(x,1): `math.ceil` also rounds negative arguments toward +infinity."""
    return math.ceil(v_rd_cs_min_kN_ / v_rd_cs1_kN_)


def resistenza_complessiva(
    v_rd_i_MPa: float, ui_mm: float, d_mm: float, n_effettivo: int, v_rd_cs1_kN_: float,
) -> tuple[float, float, float]:
    """(V'Rd,c, VRd,s, VRrd), kN."""
    v_rd_c_primo_kN = VRD_C_ENHANCEMENT_FRACTION * v_rd_i_MPa * ui_mm * d_mm / 1000.0
    v_rd_s_kN = n_effettivo * v_rd_cs1_kN_
    return v_rd_c_primo_kN, v_rd_s_kN, v_rd_c_primo_kN + v_rd_s_kN


def area_staffa_mm2(phi_staffa_mm: float) -> float:
    return bar_area(phi_staffa_mm)

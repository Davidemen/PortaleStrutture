"""Composes the taglio-non-armato steps into a Report, registered as the `ca-taglio-non-armato`
Tool (see `tool.py`). Handles both workbook sheets: `Foglio1` (v1: fck from Rck, Asl direct) and
`1m` (v2: fck direct, Asl from N°/Ø) through the same flat input model."""
from strutture.shared.report import Check, Report, success

from .asl_from_bars import asl_from_barre_mm2
from .axial_stress import sigma_cp_MPa
from .concrete_resistance import fcd_from_fck, fck_from_rck
from .effective_depth import effective_depth_mm
from .fck_consistency import avviso_incoerenza_fck_rck
from .longitudinal_ratio import rho_l, rho_l_raw
from .models import GeometriaOutput, MaterialiOutput, TaglioNonArmatoInput, TaglioNonArmatoOutput, TaglioOutput
from .shear_resistance import vrd1_kN, vrd2_kN, vrd_kN
from .size_factor import size_factor_k
from .tables import RHO_L_MAX
from .vmin import vmin_MPa


def _fck_MPa(inputs: TaglioNonArmatoInput) -> float:
    """fck from Rck (v1) unless a direct fck was given (v2, sheet `1m` B3)."""
    return inputs.fck_MPa if inputs.fck_MPa is not None else fck_from_rck(inputs.rck_MPa)


def _asl_mm2(inputs: TaglioNonArmatoInput) -> float:
    """Direct Asl (v1) unless N°/Ø were given instead (v2, sheet `1m` B13)."""
    if inputs.asl_mm2 is not None:
        return inputs.asl_mm2
    return asl_from_barre_mm2(inputs.n_barre, inputs.diametro_barre_mm)


def _avviso_fck_rck(inputs: TaglioNonArmatoInput) -> tuple[str, ...]:
    if inputs.fck_MPa is None:
        return ()
    avviso = avviso_incoerenza_fck_rck(inputs.rck_MPa, inputs.fck_MPa)
    return (avviso,) if avviso else ()


def _avviso_rho_l_capped(rho_l_raw_value: float, rho_l_capped: float, *, legacy_compat: bool) -> tuple[str, ...]:
    """Warn when the §4.1.2.3.5.1 cap actually bites in code-standard mode, since the value
    entering VRd,1 (`rho_l_capped`) then differs from the real Asl/(bw*d) ratio."""
    if legacy_compat or rho_l_raw_value <= rho_l_capped:
        return ()
    messaggio = (
        f"ρl=Asl/(bw*d)={rho_l_raw_value:.5f} supera il limite ρl,max={RHO_L_MAX} "
        f"(NTC2018 §4.1.2.3.5.1): usato ρl={rho_l_capped:.5f} nel calcolo di VRd,1."
    )
    return (messaggio,)


def _warnings(inputs: TaglioNonArmatoInput, rho_l_raw_value: float, rho_l_capped: float) -> tuple[str, ...]:
    return _avviso_fck_rck(inputs) + _avviso_rho_l_capped(rho_l_raw_value, rho_l_capped, legacy_compat=inputs.legacy_compat)


def run(inputs: TaglioNonArmatoInput) -> Report[TaglioNonArmatoOutput]:
    fck = _fck_MPa(inputs)
    fcd = fcd_from_fck(fck, gamma_c=inputs.gamma_c)
    d = effective_depth_mm(inputs.h_mm, inputs.c_mm)
    asl = _asl_mm2(inputs)
    sigma_cp = sigma_cp_MPa(inputs.ned_kN, inputs.bw_mm, inputs.h_mm, fcd)
    k = size_factor_k(d)
    vmin = vmin_MPa(k, fck)
    rl_raw = rho_l_raw(asl, inputs.bw_mm, d)
    rl = rho_l(asl, inputs.bw_mm, d, legacy_compat=inputs.legacy_compat)
    vrd1 = vrd1_kN(k, rl, fck, sigma_cp, inputs.bw_mm, d, gamma_c=inputs.gamma_c)
    vrd2 = vrd2_kN(vmin, sigma_cp, inputs.bw_mm, d)
    vrd = vrd_kN(vrd1, vrd2)

    data = TaglioNonArmatoOutput(
        materiali=MaterialiOutput(fck_MPa=fck, fcd_MPa=fcd),
        geometria=GeometriaOutput(d_mm=d, asl_mm2=asl),
        taglio=TaglioOutput(
            sigma_cp_MPa=sigma_cp,
            k=k,
            vmin_MPa=vmin,
            rho_l=rl,
            vrd1_kN=vrd1,
            vrd2_kN=vrd2,
            vrd_kN=vrd,
        ),
    )
    checks = (
        Check(
            name="Rapporto di armatura longitudinale entro il limite",
            passed=rl_raw <= RHO_L_MAX,
            detail=f"ρl={rl_raw:.5f} <= ρl,max={RHO_L_MAX}" + ("" if rl_raw == rl else f" (usato ρl={rl:.5f} in VRd,1)"),
            clause="NTC2018 §4.1.2.3.5.1",
            value=rl_raw, limit=RHO_L_MAX, unit="-",
        ),
    )
    return success(data, inputs, checks=checks, warnings=_warnings(inputs, rl_raw, rl))

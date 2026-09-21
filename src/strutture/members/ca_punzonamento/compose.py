"""Composes the ca-punzonamento steps into a Report. `run` only composes the step modules
(docs/BUILD_CONTRACT.md "Modularity"); each formula lives in its own step module."""
from strutture.shared.ec2_shear import k_size
from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.tables import exact_lookup

from . import governing_capacity as gov
from . import shear_reinf_design as design
from . import shear_reinf_layout as layout
from .column_face import faccia_pilastro, u0_mm
from .effective_depth import effective_depth
from .models import (
    ArmaturaOutput,
    GeometriaOutput,
    PerimetroCriticoOutput,
    PunzonamentoInput,
    PunzonamentoOutput,
)
from .perimeter_scan import scan_perimetro
from .reinforcement_ratio import RHO_MAX_WARNING, rho_l
from .tables import POSIZIONE_BETA

RHO_L_CLAUSE = "EN 1992-1-1 §6.4.4(1)"
FACCIA_CLAUSE = "EN 1992-1-1 §6.4.5(3)"
PERIMETRO_CLAUSE = "EN 1992-1-1 §6.4.4"
DETTAGLI_CLAUSE = "EN 1992-1-1 §9.4.3(1)"
RESISTENZA_CLAUSE = "EN 1992-1-1 §6.4.5(1)/eq.(9.11)"
ASW_MIN_CLAUSE = "EN 1992-1-1 §9.4.3(2) eq. (9.11)"


def _armatura(inputs: PunzonamentoInput, capacity: gov.GoverningCapacity, d_mm: float, k: float, rho: float) -> tuple[ArmaturaOutput, tuple[Check, ...]]:
    u0_out = layout.u0_out_mm(inputs.ved_kN, _beta(inputs), k, rho, inputs.fck_MPa, d_mm)
    k_d_primo = layout.k_d_primo_mm(u0_out, inputs.lato_a_mm, inputs.lato_b_mm)
    sr_max, a1_min, a1_max = layout.radial_limits_mm(d_mm)
    bu_st_limit = layout.bu_st_limit_mm(d_mm)
    au_mm, au_meno_a1_mm, n_file, sr_mm = layout.perimeter_rows(k_d_primo, inputs.bu_mm, inputs.a1eff_mm, sr_max)

    asw_min = design.asw_min_mm2(inputs.fck_MPa, sr_mm, inputs.st_mm)
    v_rd_cs_min = design.v_rd_cs_min_kN(capacity.v_ed_i_MPa, capacity.v_rd_i_MPa, capacity.ui_mm, d_mm)
    fywd_ef = design.fywd_ef_MPa(d_mm, legacy_compat=inputs.legacy_compat)
    area_staffa = design.area_staffa_mm2(inputs.phi_staffa_mm)
    v_rd_cs1 = design.v_rd_cs1_kN(d_mm, sr_mm, area_staffa, fywd_ef)
    n_f = design.n_f_richiesto(v_rd_cs_min, v_rd_cs1)
    v_rd_c_primo, v_rd_s, v_rrd = design.resistenza_complessiva(capacity.v_rd_i_MPa, capacity.ui_mm, d_mm, inputs.n_staffe, v_rd_cs1)
    ved_beta = inputs.ved_kN * _beta(inputs)

    armatura = ArmaturaOutput(
        u0_out_mm=u0_out, k_d_primo_mm=k_d_primo, sr_max_mm=sr_max, a1_min_mm=a1_min, a1_max_mm=a1_max,
        au_mm=au_mm, au_meno_a1_mm=au_meno_a1_mm, n_file=n_file, sr_mm=sr_mm, asw_min_mm2=asw_min,
        v_rd_cs_min_kN=v_rd_cs_min, fywd_ef_MPa=fywd_ef, area_staffa_mm2=area_staffa, v_rd_cs1_kN=v_rd_cs1,
        n_f_richiesto=n_f, n_effettivo=inputs.n_staffe, v_rd_c_primo_kN=v_rd_c_primo, v_rd_s_kN=v_rd_s,
        v_rrd_kN=v_rrd, ved_su_vrd=ved_beta / v_rrd,
    )
    checks = (
        Check(name="a1_eff_nel_range", passed=a1_min <= inputs.a1eff_mm <= a1_max, clause=DETTAGLI_CLAUSE,
              value=inputs.a1eff_mm, limit=a1_max, unit="mm", detail=f"intervallo ammesso [{a1_min:.1f}, {a1_max:.1f}] mm"),
        Check(name="bu_max", passed=inputs.bu_mm < bu_st_limit, clause=DETTAGLI_CLAUSE, value=inputs.bu_mm, limit=bu_st_limit, unit="mm"),
        Check(name="st_max", passed=inputs.st_mm < bu_st_limit, clause=DETTAGLI_CLAUSE, value=inputs.st_mm, limit=bu_st_limit, unit="mm"),
        Check(name="resistenza_con_armatura", passed=v_rrd > ved_beta, clause=RESISTENZA_CLAUSE, value=ved_beta, limit=v_rrd, unit="kN"),
        Check(name="asw_min", passed=area_staffa >= asw_min, clause=ASW_MIN_CLAUSE, value=area_staffa, limit=asw_min, unit="mm2"),
    )
    return armatura, checks


def _beta(inputs: PunzonamentoInput) -> float:
    return exact_lookup(POSIZIONE_BETA, inputs.posizione)


def run(inputs: PunzonamentoInput) -> Report[PunzonamentoOutput]:
    beta = _beta(inputs)
    dx_mm, dy_mm, d_mm = effective_depth(inputs.h_mm, inputs.copriferro_mm, inputs.phix_mm, inputs.phiy_mm)
    if d_mm <= 0:
        raise CalcError("altezza utile d non positiva: verificare H, copriferro e diametri delle armature")
    u0 = u0_mm(inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm)
    faccia = faccia_pilastro(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        u0, d_mm, inputs.fck_MPa, legacy_compat=inputs.legacy_compat, coeff_vrd_max=inputs.coeff_vrd_max,
    )
    k = k_size(d_mm)
    rho = rho_l(inputs.px_mm, inputs.py_mm, inputs.phix_mm, inputs.phiy_mm, inputs.paddx_mm, inputs.paddy_mm,
                inputs.phiaddx_mm, inputs.phiaddy_mm, d_mm)

    righe, governing = scan_perimetro(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, d_mm, k, rho, inputs.fck_MPa, legacy_compat=inputs.legacy_compat,
    )
    capacity = gov.governing_capacity(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, inputs.a_amanuale_mm2, governing.x, d_mm, k, rho, inputs.fck_MPa,
        legacy_compat=inputs.legacy_compat,
    )
    perimetro_critico = PerimetroCriticoOutput(
        righe=righe, a_governante_su_d=governing.x, a_governante_mm=capacity.a_governante_mm, ui_mm=capacity.ui_mm,
        area_mm2=capacity.area_mm2, rho=rho, k=k, ved_red_ui_kN=capacity.ved_red_ui_kN, v_rd_i_MPa=capacity.v_rd_i_MPa,
        v_ed_i_MPa=capacity.v_ed_i_MPa, rapporto=capacity.rapporto, armatura_necessaria=capacity.armatura_necessaria,
    )

    faccia_detail = "" if inputs.legacy_compat else f"vRd,max = {inputs.coeff_vrd_max:g}·ν·fcd (c scelto in input)"
    checks = (
        Check(name="punzonamento_faccia_pilastro", passed=faccia.v_ed_0_MPa < faccia.v_rd_max_MPa, clause=FACCIA_CLAUSE,
              detail=faccia_detail, value=faccia.v_ed_0_MPa, limit=faccia.v_rd_max_MPa, unit="MPa"),
        Check(name="punzonamento_perimetro_critico", passed=not capacity.armatura_necessaria, clause=PERIMETRO_CLAUSE,
              value=capacity.v_ed_i_MPa, limit=capacity.v_rd_i_MPa, unit="MPa"),
        Check(name="rho_l_massimo", passed=rho <= RHO_MAX_WARNING, clause=RHO_L_CLAUSE, value=rho, limit=RHO_MAX_WARNING, unit="-"),
    )

    armatura = None
    if inputs.legacy_compat or capacity.armatura_necessaria:
        armatura, armatura_checks = _armatura(inputs, capacity, d_mm, k, rho)
        checks = (*checks, *armatura_checks)

    data = PunzonamentoOutput(
        geometria=GeometriaOutput(dx_mm=dx_mm, dy_mm=dy_mm, d_mm=d_mm, u0_mm=u0),
        faccia_pilastro=faccia,
        perimetro_critico=perimetro_critico,
        messaggio=gov.messaggio_esito(capacity.armatura_necessaria),
        armatura=armatura,
    )
    return success(data, inputs, checks=checks)

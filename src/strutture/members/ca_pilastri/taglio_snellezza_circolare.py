"""`_nu1`, `_taglio` e `_snellezza` di pilastro-circolare, estratte da tool_circolare.py per
restare entro il limite di 150 righe per modulo (regola dura 12 di CLAUDE.md). Comportamento
identico all'originale: nessuna logica nuova."""
from strutture.shared.divergences import legacy
from strutture.shared.report import Check
from strutture.shared.section_geometry import circle

from . import limiti_ec2
from .geometria import leva_interna
from .gerarchia import domanda_taglio_capacity_design
from .models import PilastroCircolareInput, SnellezzaResult, TaglioResult
from .regole import RuleSet
from .snellezza import (
    L0_HARDCODED_LEGACY_MM,
    coefficiente_c,
    l0_effettivo_mm,
    lambda_limite,
    raggio_inerzia_netto_circolare_mm,
    snellezza,
    verifica_snellezza,
)
from .taglio_puntoni import coefficiente_ac, sigma_cp
from .taglio_resistenza import vrdc, vrds
from .taglio_theta import NU1_NTC_FISSO, cot_theta


def _nu1(inputs: PilastroCircolareInput, rules: RuleSet) -> float:
    return limiti_ec2.nu1(inputs.cls, legacy_compat=inputs.legacy_compat) if rules.nu1_ec2 else 0.5


def _taglio(inputs: PilastroCircolareInput, rules: RuleSet, ac_mm2: float, lato_equiv_mm: float, fcd_MPa: float, fyd_MPa: float) -> tuple[TaglioResult, float, Check, Check]:
    sigma_cp_MPa = sigma_cp(inputs.ned_kN, ac_mm2)
    ac_coef = coefficiente_ac(sigma_cp_MPa, fcd_MPa, legacy_compat=inputs.legacy_compat)
    z_mm = leva_interna(lato_equiv_mm, inputs.c_mm)
    nu1 = _nu1(inputs, rules)
    # See taglio_snellezza_rettangolare.py's _taglio: cotθ's own ν1 must match VRd,max's ν1; the
    # EC2 sheet's own CX42 formula hardcodes 0.5 unconditionally, so legacy_compat=True keeps 0.5.
    nu1_theta = NU1_NTC_FISSO if legacy("ca-pilastri/cot-theta-nu1-incoerente-ec2", inputs.legacy_compat) else nu1
    theta = cot_theta(inputs.diametro_staffe_mm, fyd_MPa, lato_equiv_mm, inputs.passo_staffe_mm, ac_coef, fcd_MPa, nu1=nu1_theta)
    v_rdc = vrdc(z_mm, lato_equiv_mm, ac_coef, fcd_MPa, theta, nu1=nu1)
    v_rds = vrds(z_mm, inputs.diametro_staffe_mm, inputs.passo_staffe_mm, fyd_MPa, theta)
    v_rd = min(v_rdc, v_rds)
    demand = domanda_taglio_capacity_design(inputs.mrd_kNm, inputs.h_mm, legacy_compat=inputs.legacy_compat)
    result = TaglioResult(
        sigma_cp_MPa=sigma_cp_MPa, ac=ac_coef, cot_theta=theta, vrdc_kN=v_rdc, vrds_kN=v_rds, vrd_kN=v_rd,
        domanda_capacity_design_kN=demand,
    )
    check_taglio = Check(name="Resistenza a taglio", passed=v_rd > inputs.ved_kN, clause="NTC2018 §4.1.2.1.3.2",
                          detail=f"VRd={v_rd:.3f} kN vs Ved={inputs.ved_kN} kN",
                          value=inputs.ved_kN, limit=v_rd, unit="kN")
    check_gerarchia = Check(name="Gerarchia delle resistenze a taglio", passed=v_rd > demand, clause="NTC2018 §7.4.4.2.1",
                             detail=f"VRd={v_rd:.3f} kN vs domanda={demand:.3f} kN",
                             value=demand, limit=v_rd, unit="kN")
    return result, nu1, check_taglio, check_gerarchia


def _snellezza(inputs: PilastroCircolareInput, rules: RuleSet, ac_mm2: float, fcd_MPa: float, fyd_MPa: float, as_mm2: float) -> tuple[SnellezzaResult, float, float, float | None, Check]:
    hardcode_mm = L0_HARDCODED_LEGACY_MM if inputs.norma == "NTC2008" else None
    l0_mm = l0_effettivo_mm(inputs.l0_mm, inputs.h_mm, legacy_compat=inputs.legacy_compat, hardcode_mm=hardcode_mm)
    i_mm = (
        raggio_inerzia_netto_circolare_mm(inputs.d_mm, inputs.c_mm)
        if rules.raggio_inerzia == "netto"
        else circle(inputs.d_mm).radius_of_gyration_mm
    )
    omega = None
    if rules.lambda_lim_kind == "ec2":
        omega = limiti_ec2.omega_meccanico(fyd_MPa, as_mm2, fcd_MPa, ac_mm2)
        a = limiti_ec2.coefficiente_a(inputs.phi_ef, a_fisso=rules.a_fisso)
        c = limiti_ec2.coefficiente_c(inputs.rm, c_fisso=rules.c_fisso)
        lambda_lim = limiti_ec2.lambda_limite(inputs.ned_kN, ac_mm2, fcd_MPa, omega, a=a, c=c)
    else:
        a, c = 0.7, coefficiente_c(inputs.rm)
        lambda_lim = lambda_limite(inputs.ned_kN, ac_mm2, fcd_MPa, rm=inputs.rm, legacy_compat=inputs.legacy_compat, unit_fix=rules.lambda_lim_unit_fix)
    lambda_ = snellezza(l0_mm, i_mm)
    result = SnellezzaResult(lambda_lim=lambda_lim, i_mm=i_mm, l0_mm=l0_mm, lambda_=lambda_)
    check = Check(name="Verifica di snellezza", passed=verifica_snellezza(lambda_, lambda_lim), clause="NTC2018 §4.1.2.3.9.2",
                  detail=f"λ={lambda_:.3f} vs λlim={lambda_lim:.3f}")
    return result, a, c, omega, check

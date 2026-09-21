"""Composed tool: pilastro-rettangolare — verifica di pilastro in c.a. rettangolare/quadrato in
CD "B" (NTC2018 + Circolare 7/2019, EC2 or NTC2008 per `inputs.norma`). `run` only composes the
step modules; norm-specific parameters come from `regole.resolve` (architecture-batch2.md §3)."""
import logging

from strutture.shared.report import Check, Report, success
from strutture.shared.section_geometry import rect

from . import limiti_ec2
from .armatura_minima import armatura_minima, verifica_percentuale_armatura
from .compressione import compressione_nrcd_kN, verifica_compressione
from .confinamento import altezza_critica_mm, passo_massimo_confinato_mm
from .dettagli import (
    diametro_staffe_minimo_mm,
    interasse_ferri_verticali_mm,
    interasse_staffe_massimo_mm,
    perimetro_circolare_mm,
    perimetro_rettangolare_mm,
)
from .flessione import tasso_sfruttamento_pct, verifica_flessione
from .geometria import eccentricita_minima, leva_interna, sezione_rettangolare
from .gerarchia import domanda_taglio_capacity_design
from .materiali import proprieta_materiali
from .models import (
    ArmaturaMinimaResult,
    CompressioneResult,
    ConfinamentoResult,
    DettagliResult,
    FlessioneResult,
    GeometriaResult,
    PilastroOutput,
    PilastroRettangolareInput,
    RegoleResult,
    SnellezzaResult,
    TaglioResult,
)
from .regole import RuleSet, resolve
from .schizzo import disegna_rettangolare as disegna_schizzo
from .snellezza import (
    L0_HARDCODED_LEGACY_MM,
    coefficiente_c,
    l0_effettivo_mm,
    lambda_limite,
    raggio_inerzia_netto_rettangolare_mm,
    snellezza,
    verifica_snellezza,
)
from .taglio_puntoni import coefficiente_ac, sigma_cp
from .taglio_resistenza import vrdc, vrds
from .taglio_theta import NU1_NTC_FISSO, cot_theta

logger = logging.getLogger(__name__)

AREA_MASSIMA_RATIO = 0.04  # EC2 §9.5.2(3) — riga "Area massima barre long." dedicata


def _nu1(inputs: PilastroRettangolareInput, rules: RuleSet) -> float:
    return limiti_ec2.nu1(inputs.cls, legacy_compat=inputs.legacy_compat) if rules.nu1_ec2 else 0.5


def _taglio(inputs: PilastroRettangolareInput, rules: RuleSet, ac_mm2: float, fcd_MPa: float, fyd_MPa: float) -> tuple[TaglioResult, float, Check, Check]:
    sigma_cp_MPa = sigma_cp(inputs.ned_kN, ac_mm2)
    ac_coef = coefficiente_ac(sigma_cp_MPa, fcd_MPa, legacy_compat=inputs.legacy_compat)
    z_mm = leva_interna(inputs.l2_mm, inputs.c_mm)
    nu1 = _nu1(inputs, rules)
    # cotθ's own strut-efficiency term must match the ν1 used by VRd,max (`vrdc` below) so the
    # returned θ balances VRd,s and VRd,max consistently — review finding (MEDIUM). The EC2
    # SHEET's own CX42 formula hardcodes 0.5 regardless of norma (confirmed against
    # build/cellmaps/ca-pilastri-ec2), so legacy_compat=True keeps 0.5 unconditionally.
    nu1_theta = NU1_NTC_FISSO if inputs.legacy_compat else nu1
    theta = cot_theta(inputs.diametro_staffe_mm, fyd_MPa, inputs.l1_mm, inputs.passo_staffe_mm, ac_coef, fcd_MPa, nu1=nu1_theta)
    v_rdc = vrdc(z_mm, inputs.l1_mm, ac_coef, fcd_MPa, theta, nu1=nu1)
    v_rds = vrds(z_mm, inputs.diametro_staffe_mm, inputs.passo_staffe_mm, fyd_MPa, theta)
    v_rd = min(v_rdc, v_rds)
    demand = domanda_taglio_capacity_design(inputs.mrd_kNm, inputs.h_mm, legacy_compat=inputs.legacy_compat)
    result = TaglioResult(
        sigma_cp_MPa=sigma_cp_MPa, ac=ac_coef, cot_theta=theta, vrdc_kN=v_rdc, vrds_kN=v_rds, vrd_kN=v_rd,
        domanda_capacity_design_kN=demand,
    )
    check_taglio = Check(name="taglio", passed=v_rd > inputs.ved_kN, clause="NTC2018 §4.1.2.1.3.2",
                          detail=f"VRd={v_rd:.3f} kN vs Ved={inputs.ved_kN} kN",
                          value=inputs.ved_kN, limit=v_rd, unit="kN")
    check_gerarchia = Check(name="gerarchia_resistenze", passed=v_rd > demand, clause="NTC2018 §7.4.4.2.1",
                             detail=f"VRd={v_rd:.3f} kN vs domanda={demand:.3f} kN",
                             value=demand, limit=v_rd, unit="kN")
    return result, nu1, check_taglio, check_gerarchia


def _dettagli(inputs: PilastroRettangolareInput, rules: RuleSet, ac_mm2: float, as_min_mm2: float, as_mm2: float) -> tuple[DettagliResult, tuple[Check, ...]]:
    perimetro_mm = (
        perimetro_circolare_mm(inputs.l1_mm, inputs.c_mm)
        if inputs.legacy_compat
        else perimetro_rettangolare_mm(inputs.l1_mm, inputs.l2_mm, inputs.c_mm)
    )
    interasse_calc = interasse_ferri_verticali_mm(perimetro_mm, inputs.n_ferri)
    soglia_staffe = diametro_staffe_minimo_mm(inputs.diametro_ferri_mm, legacy_compat=inputs.legacy_compat, combinatore=rules.staffe_diametro_combinatore)
    dimensione_min_mm = min(inputs.l1_mm, inputs.l2_mm) if rules.staffe_min_dimensione else None
    soglia_interasse_staffe = interasse_staffe_massimo_mm(
        inputs.diametro_ferri_mm, bar_multiplier=rules.staffe_bar_multiplier, fixed_mm=rules.staffe_fixed_mm,
        dimensione_min_mm=dimensione_min_mm,
    )

    diam_staffe_ok = True if inputs.legacy_compat else soglia_staffe <= inputs.diametro_staffe_mm
    diam_long_ok = (
        inputs.diametro_ferri_mm > rules.diametro_long_min_mm
        if inputs.legacy_compat
        else inputs.diametro_ferri_mm >= rules.diametro_long_min_mm
    )
    area_min_ok = as_min_mm2 < as_mm2 if inputs.legacy_compat else as_min_mm2 <= as_mm2
    result = DettagliResult(
        diametro_long_min_mm=rules.diametro_long_min_mm, interasse_long_max_mm=rules.long_bar_max_spacing_mm,
        interasse_long_calcolato_mm=interasse_calc, as_long_min_mm2=as_min_mm2,
        diametro_staffe_min_mm=soglia_staffe, interasse_staffe_max_mm=soglia_interasse_staffe,
    )
    checks = (
        Check(name="diametro_minimo_longitudinale", passed=diam_long_ok, clause="NTC2018 §4.1.6.1.2"),
        Check(name="interasse_massimo_longitudinale", passed=interasse_calc <= rules.long_bar_max_spacing_mm, clause="NTC2018 §7.4.6.2.2"),
        Check(name="area_minima_longitudinale", passed=area_min_ok, clause="NTC2018 §7.4.6.2.1"),
        Check(
            name="diametro_minimo_staffe", passed=diam_staffe_ok, clause="NTC2018 §7.4.6.2.2",
            detail="" if not inputs.legacy_compat else "legacy: confronto col foglio contro una cella non numerica, sempre vero",
        ),
        Check(name="interasse_massimo_staffe", passed=inputs.passo_staffe_mm <= soglia_interasse_staffe, clause="NTC2018 §7.4.6.2.2"),
    )
    if rules.as_max_check:
        as_max_mm2 = AREA_MASSIMA_RATIO * ac_mm2
        checks = (*checks, Check(name="area_massima_longitudinale", passed=as_mm2 <= as_max_mm2, clause="EC2 §9.5.2(3)",
                                  value=as_mm2, limit=as_max_mm2, unit="mm2"))
    return result, checks


def _snellezza(inputs: PilastroRettangolareInput, rules: RuleSet, ac_mm2: float, fcd_MPa: float, fyd_MPa: float, as_mm2: float) -> tuple[SnellezzaResult, float, float, float | None, Check]:
    # l0_effettivo_mm's own kwarg default (hardcode_mm=3000) reproduces the NTC2008 sheet's
    # hardcoded l0; the NTC2018/EC2 sheets already compute l0=H*beta (beta=1) even under
    # legacy_compat=True, so they default to the clear height like the code-standard branch.
    hardcode_mm = L0_HARDCODED_LEGACY_MM if inputs.norma == "NTC2008" else None
    l0_mm = l0_effettivo_mm(inputs.l0_mm, inputs.h_mm, legacy_compat=inputs.legacy_compat, hardcode_mm=hardcode_mm)
    i_mm = (
        raggio_inerzia_netto_rettangolare_mm(inputs.l1_mm, inputs.l2_mm, inputs.c_mm)
        if rules.raggio_inerzia == "netto"
        else rect(inputs.l1_mm, inputs.l2_mm).radius_of_gyration_mm
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
    check = Check(name="snellezza", passed=verifica_snellezza(lambda_, lambda_lim), clause="NTC2018 §4.1.2.3.9.2",
                  detail=f"λ={lambda_:.3f} vs λlim={lambda_lim:.3f}")
    return result, a, c, omega, check


def run_pilastro_rettangolare(inputs: PilastroRettangolareInput) -> Report[PilastroOutput]:
    rules = resolve(inputs.norma, inputs.legacy_compat)
    materiali = proprieta_materiali(inputs.acciaio, inputs.cls, legacy_compat=inputs.legacy_compat)
    ac_mm2, as_mm2, rs = sezione_rettangolare(inputs.l1_mm, inputs.l2_mm, inputs.n_ferri, inputs.diametro_ferri_mm)
    e_min_mm, med_ecc_kNm, med_calc_kNm = eccentricita_minima(max(inputs.l1_mm, inputs.l2_mm), inputs.ned_kN, inputs.med_kNm)
    geometria = GeometriaResult(ac_mm2=ac_mm2, as_mm2=as_mm2, rs=rs, e_min_mm=e_min_mm, med_ecc_kNm=med_ecc_kNm, med_calc_kNm=med_calc_kNm)

    as_min_mm2, rs_min = armatura_minima(
        ac_mm2, inputs.ned_kN, materiali.fyd_MPa, legacy_compat=inputs.legacy_compat,
        area_ratio=rules.as_min_area_ratio, combinatore=rules.as_min_combinatore,
    )
    armatura_min_result = ArmaturaMinimaResult(as_min_mm2=as_min_mm2, rs_min=rs_min)
    check_percentuale = Check(
        name="percentuale_armatura", passed=verifica_percentuale_armatura(rs, rs_min, controlla_minimo=rules.rs_controlla_minimo),
        clause="NTC2018 §7.4.6.2.1", detail=f"ρs={rs:.4f}, minimo={rs_min:.4f}, massimo=0.04",
    )

    taglio_result, nu1, check_taglio, check_gerarchia = _taglio(inputs, rules, ac_mm2, materiali.fcd_MPa, materiali.fyd_MPa)

    flessione = FlessioneResult(mrd_kNm=inputs.mrd_kNm, med_kNm=med_calc_kNm, tasso_sfruttamento_pct=tasso_sfruttamento_pct(med_calc_kNm, inputs.mrd_kNm))
    check_flessione = Check(name="flessione", passed=verifica_flessione(inputs.mrd_kNm, med_calc_kNm), clause="NTC2018 §4.1.2.1.2",
                             value=med_calc_kNm, limit=inputs.mrd_kNm, unit="kNm")

    nrcd_kN = compressione_nrcd_kN(ac_mm2, materiali.fcd_MPa)
    compressione = CompressioneResult(nrcd_kN=nrcd_kN, tasso_sfruttamento_pct=tasso_sfruttamento_pct(inputs.ned_kN, nrcd_kN))
    check_compressione = Check(name="compressione", passed=verifica_compressione(nrcd_kN, inputs.ned_kN), clause="NTC2018 §4.1.2.1.2",
                                value=inputs.ned_kN, limit=nrcd_kN, unit="kN")

    confinamento = ConfinamentoResult(
        hcr_mm=altezza_critica_mm(inputs.h_mm, max(inputs.l1_mm, inputs.l2_mm)),
        passo_max_confinato_mm=passo_massimo_confinato_mm(min(inputs.l1_mm, inputs.l2_mm), inputs.diametro_ferri_mm),
    )
    check_confinamento = Check(
        name="passo_staffe_zona_critica", passed=inputs.passo_staffe_mm <= confinamento.passo_max_confinato_mm,
        clause="NTC2018 §7.4.6.2.2", detail=f"s={inputs.passo_staffe_mm} mm vs s_max={confinamento.passo_max_confinato_mm:.3f} mm (zona critica)",
        value=inputs.passo_staffe_mm, limit=confinamento.passo_max_confinato_mm, unit="mm",
    )

    snellezza_result, a_snellezza, c_snellezza, omega, check_snellezza = _snellezza(inputs, rules, ac_mm2, materiali.fcd_MPa, materiali.fyd_MPa, as_mm2)
    dettagli_result, dettagli_checks = _dettagli(inputs, rules, ac_mm2, as_min_mm2, as_mm2)
    regole_result = RegoleResult(
        norma=inputs.norma, legacy_compat=inputs.legacy_compat, a_snellezza=a_snellezza, c_snellezza=c_snellezza,
        omega_meccanico=omega, nu1=nu1,
    )

    try:
        schizzo = disegna_schizzo(inputs)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per pilastro-rettangolare")
        schizzo = None

    output = PilastroOutput(
        materiali=materiali, geometria=geometria, armatura_minima=armatura_min_result, taglio=taglio_result,
        flessione=flessione, compressione=compressione, confinamento=confinamento, snellezza=snellezza_result,
        dettagli=dettagli_result, regole=regole_result, schizzo=schizzo,
    )
    checks = (
        check_taglio, check_gerarchia, check_percentuale, check_flessione, check_compressione,
        check_snellezza, check_confinamento, *dettagli_checks,
    )
    return success(output, inputs, checks=checks)

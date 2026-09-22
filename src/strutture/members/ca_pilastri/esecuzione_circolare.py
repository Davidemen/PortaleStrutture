"""Passi di calcolo di pilastro-circolare, estratti da tool_circolare.py per restare entro i limiti
di dimensione di modulo/funzione (regola dura 12 di CLAUDE.md). Comportamento identico
all'originale: nessuna logica nuova. Lo schizzo resta nel modulo del tool (serve al monkeypatch di
`disegna_schizzo` in tests/members/ca_pilastri/test_schizzo.py). `_nu1`/`_taglio`/`_snellezza`
vivono in taglio_snellezza_circolare.py per lo stesso motivo di dimensione."""
from dataclasses import dataclass

from strutture.shared.report import Check

from .armatura_minima import armatura_minima, verifica_percentuale_armatura
from .compressione import compressione_nrcd_kN, verifica_compressione
from .confinamento import altezza_critica_mm, passo_massimo_confinato_mm
from .dettagli_circolare import _dettagli
from .flessione import tasso_sfruttamento_pct, verifica_flessione
from .geometria import eccentricita_minima, sezione_circolare
from .models import (
    ArmaturaMinimaResult,
    CompressioneResult,
    ConfinamentoResult,
    FlessioneResult,
    GeometriaResult,
    MaterialiResult,
    PilastroCircolareInput,
    RegoleResult,
    TaglioResult,
)
from .nucleo import NucleoPilastro
from .regole import RuleSet
from .taglio_snellezza_circolare import _snellezza, _taglio


def _geometria_e_armatura(inputs: PilastroCircolareInput, rules: RuleSet, materiali: MaterialiResult) -> tuple[GeometriaResult, ArmaturaMinimaResult, float, float, float, Check]:
    ac_mm2, as_mm2, rs, lato_equiv_mm = sezione_circolare(inputs.d_mm, inputs.n_ferri, inputs.diametro_ferri_mm)
    e_min_mm, med_ecc_kNm, med_calc_kNm = eccentricita_minima(inputs.d_mm, inputs.ned_kN, inputs.med_kNm)
    geometria = GeometriaResult(ac_mm2=ac_mm2, as_mm2=as_mm2, rs=rs, e_min_mm=e_min_mm, med_ecc_kNm=med_ecc_kNm,
                                 med_calc_kNm=med_calc_kNm, lato_equivalente_mm=lato_equiv_mm)

    as_min_mm2, rs_min = armatura_minima(
        ac_mm2, inputs.ned_kN, materiali.fyd_MPa, legacy_compat=inputs.legacy_compat,
        area_ratio=rules.as_min_area_ratio, combinatore=rules.as_min_combinatore,
    )
    armatura_min_result = ArmaturaMinimaResult(as_min_mm2=as_min_mm2, rs_min=rs_min)
    check_percentuale = Check(
        name="Percentuale di armatura longitudinale", passed=verifica_percentuale_armatura(rs, rs_min, controlla_minimo=rules.rs_controlla_minimo),
        clause="NTC2018 §7.4.6.2.2", detail=f"ρs={rs:.4f}, minimo={rs_min:.4f}, massimo=0.04",
    )
    return geometria, armatura_min_result, ac_mm2, as_mm2, lato_equiv_mm, check_percentuale


@dataclass(frozen=True)
class _VerificheResistenza:
    taglio: TaglioResult
    nu1: float
    check_taglio: Check
    check_gerarchia: Check
    flessione: FlessioneResult
    check_flessione: Check
    compressione: CompressioneResult
    check_compressione: Check
    confinamento: ConfinamentoResult
    check_confinamento: Check


def _verifiche_resistenza(inputs: PilastroCircolareInput, rules: RuleSet, ac_mm2: float, lato_equiv_mm: float, materiali: MaterialiResult, med_calc_kNm: float) -> _VerificheResistenza:
    taglio_result, nu1, check_taglio, check_gerarchia = _taglio(inputs, rules, ac_mm2, lato_equiv_mm, materiali.fcd_MPa, materiali.fyd_MPa)

    flessione = FlessioneResult(mrd_kNm=inputs.mrd_kNm, med_kNm=med_calc_kNm, tasso_sfruttamento_pct=tasso_sfruttamento_pct(med_calc_kNm, inputs.mrd_kNm))
    check_flessione = Check(name="Resistenza a pressoflessione", passed=verifica_flessione(inputs.mrd_kNm, med_calc_kNm), clause="NTC2018 §4.1.2.1.2",
                             value=med_calc_kNm, limit=inputs.mrd_kNm, unit="kNm")

    nrcd_kN = compressione_nrcd_kN(ac_mm2, materiali.fcd_MPa)
    compressione = CompressioneResult(nrcd_kN=nrcd_kN, tasso_sfruttamento_pct=tasso_sfruttamento_pct(inputs.ned_kN, nrcd_kN))
    check_compressione = Check(name="Resistenza a compressione", passed=verifica_compressione(nrcd_kN, inputs.ned_kN), clause="NTC2018 §4.1.2.1.2",
                                value=inputs.ned_kN, limit=nrcd_kN, unit="kN")

    confinamento = ConfinamentoResult(
        hcr_mm=altezza_critica_mm(inputs.h_mm, inputs.d_mm),
        passo_max_confinato_mm=passo_massimo_confinato_mm(lato_equiv_mm, inputs.diametro_ferri_mm),
    )
    check_confinamento = Check(
        name="Passo delle staffe in zona critica", passed=inputs.passo_staffe_mm <= confinamento.passo_max_confinato_mm,
        clause="NTC2018 §7.4.6.2.2", detail=f"s={inputs.passo_staffe_mm} mm vs s_max={confinamento.passo_max_confinato_mm:.3f} mm (zona critica)",
        value=inputs.passo_staffe_mm, limit=confinamento.passo_max_confinato_mm, unit="mm",
    )
    return _VerificheResistenza(
        taglio=taglio_result, nu1=nu1, check_taglio=check_taglio, check_gerarchia=check_gerarchia,
        flessione=flessione, check_flessione=check_flessione, compressione=compressione,
        check_compressione=check_compressione, confinamento=confinamento, check_confinamento=check_confinamento,
    )


def calcola_nucleo_circolare(inputs: PilastroCircolareInput, rules: RuleSet, materiali: MaterialiResult) -> NucleoPilastro:
    geometria, armatura_min_result, ac_mm2, as_mm2, lato_equiv_mm, check_percentuale = _geometria_e_armatura(inputs, rules, materiali)
    vr = _verifiche_resistenza(inputs, rules, ac_mm2, lato_equiv_mm, materiali, geometria.med_calc_kNm)
    snellezza_result, a_snellezza, c_snellezza, omega, check_snellezza = _snellezza(inputs, rules, ac_mm2, materiali.fcd_MPa, materiali.fyd_MPa, as_mm2)
    dettagli_result, dettagli_checks = _dettagli(inputs, rules, ac_mm2, armatura_min_result.as_min_mm2, as_mm2)
    regole_result = RegoleResult(
        norma=inputs.norma, legacy_compat=inputs.legacy_compat, a_snellezza=a_snellezza, c_snellezza=c_snellezza,
        omega_meccanico=omega, nu1=vr.nu1,
    )
    checks = (
        vr.check_taglio, vr.check_gerarchia, check_percentuale, vr.check_flessione, vr.check_compressione,
        check_snellezza, vr.check_confinamento, *dettagli_checks,
    )
    return NucleoPilastro(
        geometria=geometria, armatura_minima=armatura_min_result, taglio=vr.taglio, flessione=vr.flessione,
        compressione=vr.compressione, confinamento=vr.confinamento, snellezza=snellezza_result,
        dettagli=dettagli_result, regole=regole_result, checks=checks,
    )

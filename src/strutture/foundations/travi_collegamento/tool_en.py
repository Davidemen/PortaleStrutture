"""Composes the EN1998 branch of `fond-trave-collegamento` (sheet `Travi colleg. EN 1998-1 e 5`)."""
from strutture.shared.report import Report, success

from .armatura_minima_en import armatura_minima_en
from .azione import azione
from .compressione import compressione
from .geometria_minima_en import geometria_minima_en
from .materiali import materiali
from .models import TraviCollegamentoInput
from .output import MinimiEnResult, TraviCollegamentoOutput
from .sismica_en import sismica_en
from .snellezza_en import snellezza_en
from .staffe_minime_en import staffe_minime_en
from .trazione import trazione

ALPHA_STAFFA_DEG_DEFAULT_EN = 90.0  # sheet C58 default — staffe verticali.


def run_en(inputs: TraviCollegamentoInput) -> Report[TraviCollegamentoOutput]:
    assert inputs.ms is not None and inputs.n_piani is not None  # enforced by the input validator
    alpha_staffa_deg = inputs.alpha_staffa_deg or ALPHA_STAFFA_DEG_DEFAULT_EN
    sismica = sismica_en(inputs.categoria_sottosuolo, inputs.ms, inputs.ag_g, legacy_compat=inputs.legacy_compat)
    mat = materiali(
        inputs.b_mm, inputs.h_mm, inputs.phi_mm, inputs.n_barre,
        inputs.classe_calcestruzzo, inputs.classe_acciaio, legacy_compat=inputs.legacy_compat,
    )
    az = azione(inputs.n1_kN, inputs.n2_kN, sismica.amax_g, sismica.alpha)
    comp = compressione(mat.ac_mm2, mat.fcd_MPa, az.ned_kN)
    traz = trazione(mat.as_mm2, mat.fyd_MPa, az.ned_kN, comp.tasso_lavoro, legacy_compat=inputs.legacy_compat)
    snel = snellezza_en(inputs.b_mm, inputs.h_mm, inputs.l_mm, inputs.beta, az.ned_kN, mat.ac_mm2, mat.fcd_MPa, mat.as_mm2, mat.fyd_MPa)
    armatura_min = armatura_minima_en(mat.ac_mm2, mat.as_mm2)
    geom_min = geometria_minima_en(inputs.b_mm, inputs.h_mm, inputs.n_piani)
    staffe_min = staffe_minime_en(
        inputs.b_mm, inputs.h_mm, inputs.cf_mm, inputs.phi_staffa_mm, inputs.n_bracci, inputs.p_mm,
        alpha_staffa_deg, mat.fck_MPa, mat.fyk_MPa,
    )
    data = TraviCollegamentoOutput(
        sismica_en=sismica, azione=az, materiali=mat, compressione=comp, trazione=traz, snellezza_en=snel,
        minimi_en=MinimiEnResult(armatura_longitudinale=armatura_min, geometria=geom_min, staffe=staffe_min),
    )
    checks = (
        comp.verifica, traz.verifica, snel.verifica, armatura_min.verifica,
        geom_min.verifica_base, geom_min.verifica_altezza, staffe_min.verifica,
    )
    return success(data, inputs, checks=checks)

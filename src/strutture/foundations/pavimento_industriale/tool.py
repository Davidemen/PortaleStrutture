"""Tool registration: `fond-pavimento-industriale` — one composed tool covering the whole
`carichi_distribuiti_concentrati` sheet (materiali + sottofondo + carico distribuito + carichi
concentrati + giunti), per architecture-batch2.md §1 `foundations/pavimento_industriale`."""
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .armatura import armatura
from .concentrati import concentrati
from .distribuiti_carico import carico_distribuito
from .distribuiti_momenti import momenti_distribuito
from .distribuiti_verifiche import verifiche_distribuito
from .giunti import giunti
from .materiali import materiali
from .models import PavimentoIndustrialeInput
from .output import DistribuitiResult, PavimentoIndustrialeOutput
from .sottofondo import sottofondo

ESEMPIO = {
    "classe_calcestruzzo": "C25/30", "gamma_c": 1.5, "gamma_s": 1.15, "nu_poisson": 0.2,
    "sottofondo_tipo": "materiale di riporto costipato", "kt_manuale_N_mm3": None,
    "h_mm": 200, "c_mm": 30, "phi_rete_mm": 8, "passo_rete_mm": 200,
    "g_daN_m2": 0.0, "gamma_g": 1.3, "q_daN_m2": 2600, "gamma_q": 1.5, "psi1_distribuito": 0.9,
    "carichi": [
        {"caso": "ruota motrice", "posizione": "centro", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "bordo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "spigolo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruote anteriori", "posizione": "centro", "p_kN": 8.0, "impronta_a_mm": 100, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
    ],
    "a_contrazione_m": 20, "b_contrazione_m": 18, "a_isolamento_m": 30.9, "b_isolamento_m": 21.2,
    "alpha_termico": 1e-5, "delta_t_C": 30,
}


def run(inputs: PavimentoIndustrialeInput) -> Report[PavimentoIndustrialeOutput]:
    mat = materiali(inputs.classe_calcestruzzo, inputs.gamma_c, inputs.gamma_s)
    sott = sottofondo(
        inputs.h_mm, inputs.c_mm, inputs.nu_poisson, mat.ecm_MPa, mat.fck_MPa,
        sottofondo_tipo=inputs.sottofondo_tipo, kt_manuale_N_mm3=inputs.kt_manuale_N_mm3,
    )
    arm = armatura(inputs.phi_rete_mm, inputs.passo_rete_mm, sott.d_mm, mat.fyd_MPa)

    carico = carico_distribuito(inputs.g_daN_m2, inputs.q_daN_m2, inputs.gamma_g, inputs.gamma_q, inputs.psi1_distribuito)
    momenti = momenti_distribuito(carico.q_slu_kN_m2, carico.q_sle_freq_kN_m2, sott.lambda_mm1)
    verifiche = verifiche_distribuito(
        momenti.m_slu_sup_Nmm_m, momenti.m_slu_inf_Nmm_m, momenti.m_sle_freq_sup_Nmm_m, momenti.m_sle_freq_inf_Nmm_m,
        sott.w_mm3_m, mat.fcfk_MPa, mat.fcfd_MPa, mat.fctm_MPa, arm.mrd_Nmm_m, legacy_compat=inputs.legacy_compat,
    )
    distribuiti_result = DistribuitiResult(carico=carico, momenti=momenti, verifiche=verifiche)

    concentrati_result, concentrati_checks = concentrati(
        inputs.carichi, inputs.h_mm, sott.l_mm, mat.fcfd_MPa, mat.fctm_MPa, arm.mrd_Nmm_m,
        sott.d_mm, sott.v1, mat.fcd_MPa, sott.v_min_MPa, legacy_compat=inputs.legacy_compat,
        coeff_vrd_max=inputs.coeff_vrd_max,
    )

    giunti_result = giunti(
        inputs.a_contrazione_m, inputs.b_contrazione_m, inputs.a_isolamento_m, inputs.b_isolamento_m,
        inputs.alpha_termico, inputs.delta_t_C, inputs.h_mm,
    )

    data = PavimentoIndustrialeOutput(
        materiali=mat, sottofondo=sott, armatura=arm,
        distribuiti=distribuiti_result, concentrati=concentrati_result, giunti=giunti_result,
    )
    checks = (
        verifiche.verifica_tensionale_sup, verifiche.verifica_tensionale_inf,
        verifiche.verifica_fessurazione_sup, verifiche.verifica_fessurazione_inf,
        verifiche.verifica_armatura_sup, verifiche.verifica_armatura_inf,
        *concentrati_checks,
        giunti_result.verifica_contrazione, giunti_result.verifica_isolamento,
    )
    return success(data, inputs, checks=checks)


TOOLS = (
    Tool(
        name="fond-pavimento-industriale",
        title="Verifica pavimento industriale su sottofondo Winkler (CNR-DT 211/2014)",
        group="Fondazioni / Pavimenti industriali",
        norm="CNR-DT 211/2014 · EC2 §6.4",
        input_model=PavimentoIndustrialeInput,
        output_model=PavimentoIndustrialeOutput,
        run=run,
        example=ESEMPIO,
    ),
)

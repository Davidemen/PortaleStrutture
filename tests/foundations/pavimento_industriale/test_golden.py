"""Golden test: `docs/specs/pavimento-industriale.md` §"Golden test case", `legacy_compat=True`."""
import pytest

from strutture.foundations.pavimento_industriale.models import PavimentoIndustrialeInput
from strutture.foundations.pavimento_industriale.tool import run

_INPUTS = {
    "classe_calcestruzzo": "C25/30", "gamma_c": 1.5, "gamma_s": 1.15, "nu_poisson": 0.2,
    "sottofondo_tipo": "materiale di riporto costipato", "kt_manuale_N_mm3": None,
    "h_mm": 200, "c_mm": 30, "phi_rete_mm": 8, "passo_rete_mm": 200,
    "g_daN_m2": 0.0, "gamma_g": 1.3, "q_daN_m2": 2600, "gamma_q": 1.5, "psi1_distribuito": 0.9,
    "carichi": [
        {"caso": "ruota motrice", "posizione": "centro", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "bordo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "spigolo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
    ],
    "a_contrazione_m": 20, "b_contrazione_m": 18, "a_isolamento_m": 30.9, "b_isolamento_m": 21.2,
    "alpha_termico": 1e-5, "delta_t_C": 30,
    "legacy_compat": True,
}


@pytest.mark.golden
def test_golden_case() -> None:
    report = run(PavimentoIndustrialeInput(**_INPUTS))
    assert report.ok
    data = report.data

    mat = data.materiali
    assert mat.rck_MPa == pytest.approx(30.0)
    assert mat.fck_MPa == pytest.approx(25.0)
    assert mat.fcd_MPa == pytest.approx(14.1667, rel=1e-5)
    assert mat.fcm_MPa == pytest.approx(33.0)
    assert mat.fctm_MPa == pytest.approx(2.60682, rel=1e-5)
    assert mat.fcfm_MPa == pytest.approx(3.12819, rel=1e-5)
    assert mat.fcfk_MPa == pytest.approx(2.18973, rel=1e-5)
    assert mat.fcfd_MPa == pytest.approx(1.45982, rel=1e-5)
    assert mat.ecm_MPa == pytest.approx(31475.8, rel=1e-5)
    assert mat.fyk_MPa == pytest.approx(450.0)
    assert mat.fyd_MPa == pytest.approx(391.304, rel=1e-5)

    sott = data.sottofondo
    assert sott.kt_N_mm3 == pytest.approx(0.06)
    assert sott.d_mm == pytest.approx(170.0)
    assert sott.lambda_mm1 == pytest.approx(0.000919499, rel=1e-5)
    assert sott.w_mm3_m == pytest.approx(6.66667e6, rel=1e-5)
    assert sott.l_mm == pytest.approx(776.901, rel=1e-5)
    assert sott.k_ec2 == pytest.approx(2.0)
    assert sott.v_min_MPa == pytest.approx(0.494975, rel=1e-5)
    assert sott.v1 == pytest.approx(0.54, rel=1e-5)

    dist = data.distribuiti
    assert dist.carico.q_slu_kN_m2 == pytest.approx(39.0)
    assert dist.carico.q_sle_freq_kN_m2 == pytest.approx(23.4)
    assert dist.momenti.m_slu_sup_Nmm_m == pytest.approx(7758.68, rel=1e-5)
    assert dist.momenti.m_slu_inf_Nmm_m == pytest.approx(7435.78, rel=1e-5)
    assert dist.momenti.m_sle_freq_sup_Nmm_m == pytest.approx(4655.21, rel=1e-5)
    assert dist.momenti.m_sle_freq_inf_Nmm_m == pytest.approx(4461.47, rel=1e-5)
    assert dist.verifiche.sigma_c_max_sup_MPa == pytest.approx(1.1638, rel=1e-5)
    assert dist.verifiche.sigma_c_max_inf_MPa == pytest.approx(1.11537, rel=1e-5)
    assert dist.verifiche.sigma_c_t_sup_MPa == pytest.approx(0.698281, rel=1e-5)
    assert dist.verifiche.sigma_c_t_inf_MPa == pytest.approx(0.669221, rel=1e-5)
    assert data.armatura.as_mm2_m == pytest.approx(251.327, rel=1e-5)
    assert data.armatura.mrd_Nmm_m == pytest.approx(15046.9, rel=1e-5)
    assert all(check.passed for check in report.checks)

    centro = next(r for r in data.concentrati.righe if r.posizione == "centro")
    spigolo = next(r for r in data.concentrati.righe if r.posizione == "spigolo")
    assert centro.sigma_c_max_MPa == pytest.approx(0.789861, rel=1e-5)
    assert centro.tl_tensionale == pytest.approx(0.541068, rel=1e-4)
    assert centro.tl_punzonamento_u0 == pytest.approx(0.0342657, rel=1e-4)
    assert centro.tl_punzonamento_u1 == pytest.approx(0.0952414, rel=1e-4)
    assert spigolo.sigma_c_max_MPa == pytest.approx(1.02311, rel=1e-5)
    assert spigolo.tl_punzonamento_u1 == pytest.approx(0.33742, rel=1e-4)

    giunti = data.giunti
    assert giunti.rapporto_contrazione == pytest.approx(1.11111, rel=1e-5)
    assert giunti.l_max_contrazione_cm == pytest.approx(460.0)
    assert giunti.spessore_isolamento_mm == pytest.approx(40.0)
    assert giunti.rapporto_isolamento == pytest.approx(1.45755, rel=1e-5)
    assert giunti.apertura_dilatazione_mm == pytest.approx(9.27, rel=1e-5)

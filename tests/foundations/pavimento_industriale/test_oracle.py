"""Oracle tests for `fond-pavimento-industriale` against
`tests/fixtures/pavimento_industriale_oracle.json` (regenerate with
`PYTHONPATH=. uv run python tests/fixtures/gen_pavimento_industriale.py`).
Reads only the "ruota motrice" (K:O) concentrated-load block (see the gen script docstring)."""
import json
from pathlib import Path

import pytest

from strutture.foundations.pavimento_industriale.carico_row import CaricoRow
from strutture.foundations.pavimento_industriale.models import PavimentoIndustrialeInput
from strutture.foundations.pavimento_industriale.tool import run

FIXTURE = json.loads(Path(__file__).parents[2].joinpath("fixtures", "pavimento_industriale_oracle.json").read_text(encoding="utf-8"))

_DEFAULTS = {
    "C4": "C25/30", "C24": "materiale di riporto costipato", "C27": 200, "C28": 30,
    "G4": 0, "G6": 2600,
    "L5": 15.5, "L6": 1.5, "L7": 0.9, "M5": 15.5, "M6": 1.5, "M7": 0.9, "N5": 15.5, "N6": 1.5, "N7": 0.9,
    "L10": 500, "M10": 500, "N10": 500, "L11": 100, "M11": 100, "N11": 100,
}
_POSIZIONI = {"L": "centro", "M": "bordo", "N": "spigolo"}
_ESITO = {"OK": True, "ATTENZIONE": False}


def _to_input(cells: dict) -> PavimentoIndustrialeInput:
    merged = {**_DEFAULTS, **cells}
    carichi = tuple(
        CaricoRow(
            caso="ruota motrice", posizione=posizione, p_kN=merged[f"{col}5"], gamma=merged[f"{col}6"],
            psi1=merged[f"{col}7"], impronta_a_mm=merged[f"{col}10"], impronta_b_mm=merged[f"{col}11"],
        )
        for col, posizione in _POSIZIONI.items()
    )
    return PavimentoIndustrialeInput(
        classe_calcestruzzo=merged["C4"], sottofondo_tipo=merged["C24"], kt_manuale_N_mm3=None,
        h_mm=merged["C27"], c_mm=merged["C28"], phi_rete_mm=8, passo_rete_mm=200,
        g_daN_m2=merged["G4"], q_daN_m2=merged["G6"], carichi=carichi,
        a_contrazione_m=20, b_contrazione_m=18, a_isolamento_m=30.9, b_isolamento_m=21.2,
        alpha_termico=1e-5, delta_t_C=30, legacy_compat=True,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle(case: dict) -> None:
    outputs = case["outputs"]
    report = run(_to_input(case["inputs"]))
    assert report.ok
    data = report.data

    mat = data.materiali
    assert mat.rck_MPa == pytest.approx(outputs["C5"], rel=1e-5)
    assert mat.fck_MPa == pytest.approx(outputs["C6"], rel=1e-5)
    assert mat.fcd_MPa == pytest.approx(outputs["C8"], rel=1e-5)
    assert mat.fcm_MPa == pytest.approx(outputs["C9"], rel=1e-5)
    assert mat.fctm_MPa == pytest.approx(outputs["C10"], rel=1e-5)
    assert mat.fcfm_MPa == pytest.approx(outputs["C11"], rel=1e-5)
    assert mat.fcfk_MPa == pytest.approx(outputs["C12"], rel=1e-5)
    assert mat.fcfd_MPa == pytest.approx(outputs["C13"], rel=1e-5)
    assert mat.ecm_MPa == pytest.approx(outputs["C14"], rel=1e-5)
    assert mat.fyk_MPa == pytest.approx(outputs["C19"], rel=1e-5)
    assert mat.fyd_MPa == pytest.approx(outputs["C21"], rel=1e-5)

    sott = data.sottofondo
    assert sott.kt_N_mm3 == pytest.approx(outputs["C26"], rel=1e-5)
    assert sott.d_mm == pytest.approx(outputs["C29"], rel=1e-5)
    assert sott.lambda_mm1 == pytest.approx(outputs["C30"], rel=1e-4)
    assert sott.w_mm3_m == pytest.approx(outputs["C31"], rel=1e-5)
    assert sott.l_mm == pytest.approx(outputs["C32"], rel=1e-5)
    assert sott.k_ec2 == pytest.approx(outputs["C33"], rel=1e-5)
    assert sott.v_min_MPa == pytest.approx(outputs["C34"], rel=1e-5)
    assert sott.v1 == pytest.approx(outputs["C35"], rel=1e-5)

    dist = data.distribuiti
    assert dist.carico.q_kN_m2 == pytest.approx(outputs["G10"], rel=1e-5)
    assert dist.carico.q_slu_kN_m2 == pytest.approx(outputs["G11"], rel=1e-5)
    assert dist.carico.q_sle_freq_kN_m2 == pytest.approx(outputs["G12"], rel=1e-5)
    assert dist.momenti.m_slu_sup_Nmm_m == pytest.approx(outputs["G16"], rel=1e-4)
    assert dist.momenti.m_slu_inf_Nmm_m == pytest.approx(outputs["H16"], rel=1e-4)
    assert dist.momenti.m_sle_freq_sup_Nmm_m == pytest.approx(outputs["G17"], rel=1e-4)
    assert dist.momenti.m_sle_freq_inf_Nmm_m == pytest.approx(outputs["H17"], rel=1e-4)
    assert dist.verifiche.sigma_c_max_sup_MPa == pytest.approx(outputs["G21"], rel=1e-4)
    assert dist.verifiche.sigma_c_max_inf_MPa == pytest.approx(outputs["H21"], rel=1e-4)
    # legacy_compat=True reproduces the sheet's inconsistent denominators (fcfk sup / fcfd inf).
    assert dist.verifiche.verifica_tensionale_sup.value / dist.verifiche.verifica_tensionale_sup.limit == pytest.approx(outputs["G22"], rel=1e-3)
    assert dist.verifiche.verifica_tensionale_inf.value / dist.verifiche.verifica_tensionale_inf.limit == pytest.approx(outputs["H22"], rel=1e-3)
    assert dist.verifiche.sigma_c_t_sup_MPa == pytest.approx(outputs["G26"], rel=1e-4)
    assert dist.verifiche.sigma_c_t_inf_MPa == pytest.approx(outputs["H26"], rel=1e-4)
    assert dist.verifiche.verifica_fessurazione_sup.value / dist.verifiche.verifica_fessurazione_sup.limit == pytest.approx(outputs["G27"], rel=1e-3)
    assert dist.verifiche.verifica_fessurazione_inf.value / dist.verifiche.verifica_fessurazione_inf.limit == pytest.approx(outputs["H27"], rel=1e-3)
    assert data.armatura.as_mm2_m == pytest.approx(outputs["G33"], rel=1e-5)
    assert data.armatura.mrd_Nmm_m == pytest.approx(outputs["G34"], rel=1e-4)
    assert dist.verifiche.verifica_armatura_sup.value / dist.verifiche.verifica_armatura_sup.limit == pytest.approx(outputs["G35"], rel=1e-3)
    assert dist.verifiche.verifica_armatura_inf.value / dist.verifiche.verifica_armatura_inf.limit == pytest.approx(outputs["H35"], rel=1e-3)

    for col, posizione in _POSIZIONI.items():
        riga = next(r for r in data.concentrati.righe if r.posizione == posizione)
        assert riga.ac_mm2 == pytest.approx(outputs[f"{col}12"], rel=1e-5)
        assert riga.b_mm == pytest.approx(outputs[f"{col}14"], rel=1e-4)
        assert riga.m_slu_Nmm_m == pytest.approx(outputs[f"{col}17"], rel=1e-4)
        assert riga.sigma_c_max_MPa == pytest.approx(outputs[f"{col}22"], rel=1e-4)
        assert riga.tl_tensionale == pytest.approx(outputs[f"{col}23"], rel=1e-3)
        assert riga.v_ed_kN == pytest.approx(outputs[f"{col}28"], rel=1e-5)
        assert riga.tl_punzonamento_u0 == pytest.approx(outputs[f"{col}32"], rel=1e-3)
        assert riga.u1_mm == pytest.approx(outputs[f"{col}33"], rel=1e-4)
        assert riga.tl_punzonamento_u1 == pytest.approx(outputs[f"{col}36"], rel=1e-3)
        assert riga.sigma_c_t_MPa == pytest.approx(outputs[f"{col}40"], rel=1e-4)
        assert riga.tl_fessurazione == pytest.approx(outputs[f"{col}41"], rel=1e-3)
        assert riga.tl_armatura == pytest.approx(outputs[f"{col}49"], rel=1e-3)

    assert data.giunti.rapporto_contrazione == pytest.approx(outputs["G39"], rel=1e-5)
    assert data.giunti.verifica_contrazione.passed == _ESITO[outputs["I39"]]
    assert data.giunti.l_max_contrazione_cm == pytest.approx(outputs["G40"], rel=1e-5)
    assert data.giunti.spessore_isolamento_mm == pytest.approx(outputs["G41"], rel=1e-5)
    assert data.giunti.rapporto_isolamento == pytest.approx(outputs["G47"], rel=1e-5)
    assert data.giunti.verifica_isolamento.passed == _ESITO[outputs["I47"]]
    assert data.giunti.apertura_dilatazione_mm == pytest.approx(outputs["G50"], rel=1e-5)

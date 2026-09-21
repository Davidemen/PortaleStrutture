"""Extra golden cases — sheets "Tratto B".."Tratto E" (docs/BUILD_CONTRACT.md "Extra golden
cases"), each sheet's own cached values with an empty override. legacy_compat=True."""
import json
from pathlib import Path

import pytest

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import run_muro_sostegno

pytestmark = pytest.mark.golden

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "muro_sostegno_tratti_oracle.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))

COMBO_ROWS = [
    ("STR_1", 45, 56, 67, False),
    ("STR_2", 46, 57, 68, False),
    ("GEO_1", 47, 58, 69, False),
    ("SISMA_1", 80, 87, 94, True),
    ("SISMA_2", 81, 88, 95, True),
]


def _inputs(o: dict[str, object]) -> MuroSostegnoInput:
    return MuroSostegnoInput(
        gamma_terr_sat_kN_m3=o["I4"],
        gamma_terr_secco_kN_m3=o["I5"],
        phi_deg=o["I6"],
        delta_deg=o["I7"],
        beta_deg=o["I8"],
        psi_deg=o["I9"],
        omega_deg=o["I10"],
        ag_g=o["I15"],
        f0=o["I16"],
        categoria_sottosuolo=o["I17"],
        categoria_topografica="T1",
        beta_m=o["I21"],
        gamma_e=o["I22"],
        gamma_cls_kN_m3=o["I25"],
        s_base_m=o["I26"],
        s_top_m=o["I27"],
        s_fond_m=o["I28"],
        h_muro_m=o["I29"],
        b_valle_m=o["I31"],
        b_monte_m=o["I32"],
        q_kN_m2=o["I38"],
        copertura_paramento_m=0.06,
        grado_acciaio="B450C",
        passo_arm_paramento_m=0.2,
        copertura_fondazione_m=0.06,
        passo_arm_fondazione_m=0.2,
        legacy_compat=True,
    )


def _find(sequence, nome):
    return next(c for c in sequence if c.nome == nome)


@pytest.mark.parametrize("case", CASES, ids=[c["sheet"] for c in CASES])
@pytest.mark.parametrize("combo", COMBO_ROWS, ids=[c[0] for c in COMBO_ROWS])
def test_tratto_golden_case(case, combo):
    nome, r1, r2, r3, sismica = combo
    o = case["outputs"]
    data = run_muro_sostegno(_inputs(o)).data

    spinta = _find(data.spinte, nome)
    assert spinta.w_muro_kN == pytest.approx(o[f"G{r1}"], rel=1e-5)
    assert spinta.w_terr_kN == pytest.approx(o[f"Q{r1}"], rel=1e-5)
    assert spinta.ka == pytest.approx(o[f"B{r2}"], rel=1e-5)
    if sismica:
        assert spinta.kh == pytest.approx(o[f"Y{r1}"], rel=1e-5)
        assert spinta.kv == pytest.approx(o[f"Z{r1}"], rel=1e-5)
        assert spinta.theta_rad == pytest.approx(o[f"AA{r1}"], rel=1e-5)

    verifica = _find(data.ribaltamento_scorrimento, nome)
    assert verifica.m_rib_kNm == pytest.approx(o[f"M{r2}"], rel=1e-5)
    assert verifica.m_stab_kNm == pytest.approx(o[f"N{r2}"], rel=1e-5)
    assert verifica.or_ribaltamento == pytest.approx(o[f"O{r2}"], rel=1e-5)
    assert verifica.n_tot_kN == pytest.approx(o[f"Q{r2}"], rel=1e-5)
    assert verifica.os_scorrimento == pytest.approx(o[f"S{r2}"], rel=1e-5)

    pressioni = _find(data.pressioni_terreno, nome)
    assert pressioni.eccentricita_m == pytest.approx(o[f"O{r3}"], rel=1e-4)
    assert pressioni.b_star_m == pytest.approx(o[f"Q{r3}"], abs=1e-4)
    assert pressioni.p_valle_kPa == pytest.approx(o[f"R{r3}"], rel=1e-4)
    assert pressioni.p_monte_kPa == pytest.approx(o[f"S{r3}"], rel=1e-4, abs=1e-6)


@pytest.mark.parametrize("case", CASES, ids=[c["sheet"] for c in CASES])
def test_tratto_golden_armatura_governing(case):
    o = case["outputs"]
    data = run_muro_sostegno(_inputs(o)).data

    assert data.armatura_paramento.as_nec_cm2_m == pytest.approx(o["H151"], rel=1e-4, abs=1e-9)
    assert data.armatura_paramento.callout == o["I151"]
    assert data.armatura_fondazione_valle.as_nec_cm2_m == pytest.approx(o["K169"], rel=1e-4, abs=1e-9)
    assert data.armatura_fondazione_valle.callout == o["M169"]
    assert data.armatura_fondazione_monte.as_nec_cm2_m == pytest.approx(o["M187"], rel=1e-4, abs=1e-9)
    assert data.armatura_fondazione_monte.callout == o["N187"]

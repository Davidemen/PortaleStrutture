"""Oracle test — `muro_sostegno_oracle.json` (LibreOffice-recalculated `Muro di sostegno DM2018.xlsx`,
sheet Tratto A), legacy_compat=True. See tests/fixtures/gen_muro_sostegno_oracle.py."""
import json
from pathlib import Path

import pytest

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import run_muro_sostegno

pytestmark = pytest.mark.oracle

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "muro_sostegno_oracle.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))

# (nome combo, riga Tool1, riga Tool2/Ka, riga Tool3, riga Tool4, riga Tool5, riga Tool6, sismica)
COMBO_ROWS = [
    ("STR_1", 45, 56, 67, 143, 161, 179, False),
    ("STR_2", 46, 57, 68, 144, 162, 180, False),
    ("GEO_1", 47, 58, 69, 145, 163, 181, False),
    ("SISMA_1", 80, 87, 94, 149, 167, 185, True),
    ("SISMA_2", 81, 88, 95, 150, 168, 186, True),
]


def _inputs(raw: dict[str, object]) -> MuroSostegnoInput:
    return MuroSostegnoInput(
        gamma_terr_sat_kN_m3=raw["I4"],
        gamma_terr_secco_kN_m3=raw["I5"],
        phi_deg=raw["I6"],
        delta_deg=raw["I7"],
        beta_deg=raw["I8"],
        psi_deg=raw["I9"],
        omega_deg=raw["I10"],
        ag_g=raw["I15"],
        f0=raw["I16"],
        categoria_sottosuolo="C",
        categoria_topografica="T1",
        beta_m=raw["I21"],
        gamma_e=raw["I22"],
        gamma_cls_kN_m3=raw["I25"],
        s_base_m=raw["I26"],
        s_top_m=raw["I27"],
        s_fond_m=raw["I28"],
        h_muro_m=raw["I29"],
        b_valle_m=raw["I31"],
        b_monte_m=raw["I32"],
        q_kN_m2=raw["I38"],
        copertura_paramento_m=0.06,
        grado_acciaio="B450C",
        passo_arm_paramento_m=0.2,
        copertura_fondazione_m=0.06,
        passo_arm_fondazione_m=0.2,
        legacy_compat=True,
    )


def _find(sequence, nome):
    return next(c for c in sequence if c.nome == nome)


@pytest.mark.parametrize("case", CASES, ids=[f"case{i}" for i in range(len(CASES))])
@pytest.mark.parametrize("combo", COMBO_ROWS, ids=[c[0] for c in COMBO_ROWS])
def test_muro_sostegno_matches_libreoffice(case, combo):
    nome, r1, r2, r3, r4, r5, r6, sismica = combo
    outputs = case["outputs"]
    data = run_muro_sostegno(_inputs(case["inputs"])).data

    spinta = _find(data.spinte, nome)
    assert spinta.w_muro_kN == pytest.approx(outputs[f"G{r1}"], rel=1e-5)
    assert spinta.m_muro_kNm == pytest.approx(outputs[f"I{r1}"], rel=1e-5)
    assert spinta.phi_d_rad == pytest.approx(outputs[f"K{r1}"], rel=1e-5)
    assert spinta.delta_d_rad == pytest.approx(outputs[f"M{r1}"], abs=1e-9)
    assert spinta.w_terr_kN == pytest.approx(outputs[f"Q{r1}"], rel=1e-5)
    assert spinta.m_terr_kNm == pytest.approx(outputs[f"S{r1}"], rel=1e-5)
    assert spinta.ka == pytest.approx(outputs[f"B{r2}"], rel=1e-5)
    if sismica:
        assert spinta.kh == pytest.approx(outputs[f"Y{r1}"], rel=1e-5)
        assert spinta.kv == pytest.approx(outputs[f"Z{r1}"], rel=1e-5)
        assert spinta.theta_rad == pytest.approx(outputs[f"AA{r1}"], rel=1e-5)

    verifica = _find(data.ribaltamento_scorrimento, nome)
    assert verifica.m_rib_kNm == pytest.approx(outputs[f"M{r2}"], rel=1e-5)
    assert verifica.m_stab_kNm == pytest.approx(outputs[f"N{r2}"], rel=1e-5)
    assert verifica.or_ribaltamento == pytest.approx(outputs[f"O{r2}"], rel=1e-5)
    assert verifica.n_tot_kN == pytest.approx(outputs[f"Q{r2}"], rel=1e-5)
    assert verifica.r_tot_kN == pytest.approx(outputs[f"R{r2}"], rel=1e-5)
    assert verifica.os_scorrimento == pytest.approx(outputs[f"S{r2}"], rel=1e-5)

    pressioni = _find(data.pressioni_terreno, nome)
    assert pressioni.e_muro_m == pytest.approx(outputs[f"D{r3}"], rel=1e-5)
    assert pressioni.e_terr_m == pytest.approx(outputs[f"G{r3}"], rel=1e-5)
    assert pressioni.m_tot_kNm == pytest.approx(outputs[f"M{r3}"], rel=1e-4)
    assert pressioni.n_tot_kN == pytest.approx(outputs[f"N{r3}"], rel=1e-5)
    assert pressioni.eccentricita_m == pytest.approx(outputs[f"O{r3}"], rel=1e-4)
    assert pressioni.b_star_m == pytest.approx(outputs[f"Q{r3}"], abs=1e-4)
    assert pressioni.p_valle_kPa == pytest.approx(outputs[f"R{r3}"], rel=1e-4)
    assert pressioni.p_monte_kPa == pytest.approx(outputs[f"S{r3}"], rel=1e-4, abs=1e-6)

    paramento = _find(data.armatura_paramento.combinazioni, nome)
    assert paramento.zq_m == pytest.approx(outputs[f"C{r4}"], rel=1e-5)
    assert paramento.zterr_m == pytest.approx(outputs[f"D{r4}"], rel=1e-5)
    assert paramento.m_ed_kNm == pytest.approx(outputs[f"G{r4}"], rel=1e-4)
    assert paramento.as_nec_cm2_m == pytest.approx(outputs[f"H{r4}"], rel=1e-4, abs=1e-9)

    valle = _find(data.armatura_fondazione_valle.combinazioni, nome)
    assert valle.p_star_kPa == pytest.approx(outputs[f"F{r5}"], rel=1e-4)
    assert valle.m_ed_p1_kNm == pytest.approx(outputs[f"G{r5}"], rel=1e-4)
    assert valle.m_ed_p2_kNm == pytest.approx(outputs[f"H{r5}"], rel=1e-4, abs=1e-9)
    assert valle.m_ed_fond_kNm == pytest.approx(outputs[f"I{r5}"], rel=1e-4)
    assert valle.m_ed_tot_kNm == pytest.approx(outputs[f"J{r5}"], rel=1e-4)
    assert valle.as_nec_cm2_m == pytest.approx(outputs[f"K{r5}"], rel=1e-4, abs=1e-9)

    monte = _find(data.armatura_fondazione_monte.combinazioni, nome)
    assert monte.p_star_star_kPa == pytest.approx(outputs[f"F{r6}"], rel=1e-4)
    assert monte.m_ed_p_kNm == pytest.approx(outputs[f"G{r6}"], rel=1e-4, abs=1e-9)
    assert monte.m_ed_terr_kNm == pytest.approx(outputs[f"H{r6}"], rel=1e-4)
    assert monte.m_ed_sv_kNm == pytest.approx(outputs[f"I{r6}"], rel=1e-4, abs=1e-9)
    assert monte.m_ed_fond_kNm == pytest.approx(outputs[f"J{r6}"], rel=1e-4)
    assert monte.m_ed_tot_kNm == pytest.approx(outputs[f"K{r6}"], rel=1e-4)
    assert monte.as_nec_cm2_m == pytest.approx(outputs[f"M{r6}"], rel=1e-4, abs=1e-9)


@pytest.mark.parametrize("case", CASES, ids=[f"case{i}" for i in range(len(CASES))])
def test_muro_sostegno_armatura_governing_matches_libreoffice(case):
    outputs = case["outputs"]
    data = run_muro_sostegno(_inputs(case["inputs"])).data

    assert data.armatura_paramento.as_nec_cm2_m == pytest.approx(outputs["H151"], rel=1e-4, abs=1e-9)
    assert data.armatura_paramento.callout == outputs["I151"]
    assert data.armatura_fondazione_valle.as_nec_cm2_m == pytest.approx(outputs["K169"], rel=1e-4, abs=1e-9)
    assert data.armatura_fondazione_valle.callout == outputs["M169"]
    assert data.armatura_fondazione_monte.as_nec_cm2_m == pytest.approx(outputs["M187"], rel=1e-4, abs=1e-9)
    assert data.armatura_fondazione_monte.callout == outputs["N187"]

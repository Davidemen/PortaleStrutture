"""Golden test — Tratto A cached values (docs/specs/muro-sostegno.md §"Golden test case"), legacy_compat=True."""
import pytest

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import run_muro_sostegno

pytestmark = pytest.mark.golden

TRATTO_A_INPUT = MuroSostegnoInput(
    gamma_terr_sat_kN_m3=19.7,
    gamma_terr_secco_kN_m3=15.6,
    phi_deg=30.69,
    delta_deg=0,
    beta_deg=0,
    psi_deg=90,
    omega_deg=0,
    ag_g=0.136,
    f0=2.419,
    categoria_sottosuolo="C",
    categoria_topografica="T1",
    beta_m=0.24,
    gamma_e=1.0,
    gamma_cls_kN_m3=25,
    s_base_m=0.49,
    s_top_m=0.25,
    s_fond_m=0.3,
    h_muro_m=2.4,
    b_valle_m=0.26,
    b_monte_m=1.15,
    q_kN_m2=2,
    copertura_paramento_m=0.06,
    grado_acciaio="B450C",
    passo_arm_paramento_m=0.2,
    copertura_fondazione_m=0.06,
    passo_arm_fondazione_m=0.2,
    legacy_compat=True,
)


def _combo(sequence, nome):
    return next(c for c in sequence if c.nome == nome)


def test_golden_geometria_e_parametri_sismici():
    data = run_muro_sostegno(TRATTO_A_INPUT).data
    assert data.geometria.h_muro_tot_m == pytest.approx(2.7)
    assert data.geometria.b_fond_m == pytest.approx(1.9)
    assert data.geometria.a_muro_m2 == pytest.approx(1.458)
    assert data.geometria.x_muro_m == pytest.approx(0.661523, rel=1e-5)
    assert data.geometria.a_terr_m2 == pytest.approx(2.76)
    assert data.geometria.x_terr_m == pytest.approx(1.325)
    assert data.parametri_sismici.s == pytest.approx(1.5, rel=1e-3)


def test_golden_spinta_str1_and_sisma1():
    spinte = run_muro_sostegno(TRATTO_A_INPUT).data.spinte
    str1 = _combo(spinte, "STR_1")
    assert str1.ka == pytest.approx(0.324159, rel=1e-5)
    assert str1.w_muro_kN == pytest.approx(47.385)
    assert str1.w_terr_kN == pytest.approx(70.6836, rel=1e-5)

    sisma1 = _combo(spinte, "SISMA_1")
    assert sisma1.kh == pytest.approx(0.04896, rel=1e-5)
    assert sisma1.kv == pytest.approx(0.02448, rel=1e-5)
    assert sisma1.theta_rad == pytest.approx(0.0477538, rel=1e-5)
    assert sisma1.ka == pytest.approx(0.445069, rel=1e-5)


def test_golden_ribaltamento_scorrimento_str1_and_sisma1():
    verifiche = run_muro_sostegno(TRATTO_A_INPUT).data.ribaltamento_scorrimento
    str1 = _combo(verifiche, "STR_1")
    assert str1.m_rib_kNm == pytest.approx(30.7784, rel=1e-5)
    assert str1.m_stab_kNm == pytest.approx(125.002, rel=1e-5)
    assert str1.or_ribaltamento == pytest.approx(4.06135, rel=1e-5)
    assert str1.n_tot_kN == pytest.approx(118.069, rel=1e-5)
    assert str1.os_scorrimento == pytest.approx(2.13092, rel=1e-5)
    assert str1.verifica_ribaltamento.passed is True
    assert str1.verifica_scorrimento.passed is True

    sisma1 = _combo(verifiche, "SISMA_1")
    assert sisma1.m_rib_kNm == pytest.approx(46.1951, rel=1e-5)
    assert sisma1.m_stab_kNm == pytest.approx(96.1554, rel=1e-5)
    assert sisma1.or_ribaltamento == pytest.approx(2.08151, rel=1e-5)
    assert sisma1.n_tot_kN == pytest.approx(90.822, rel=1e-5)
    assert sisma1.os_scorrimento == pytest.approx(1.21249, rel=1e-5)


def test_golden_pressioni_terreno_str1_and_sisma1():
    pressioni = run_muro_sostegno(TRATTO_A_INPUT).data.pressioni_terreno
    str1 = _combo(pressioni, "STR_1")
    assert str1.eccentricita_m == pytest.approx(0.151959, rel=1e-5)
    assert str1.entro_nocciolo is True
    assert str1.p_valle_kPa == pytest.approx(91.9612, rel=1e-5)
    assert str1.p_monte_kPa == pytest.approx(32.3216, rel=1e-5)

    sisma1 = _combo(pressioni, "SISMA_1")
    assert sisma1.eccentricita_m == pytest.approx(0.399909, rel=1e-5)
    assert sisma1.entro_nocciolo is False
    assert sisma1.b_star_m == pytest.approx(1.65027, rel=1e-5)
    assert sisma1.p_valle_kPa == pytest.approx(110.069, rel=1e-5)
    assert sisma1.p_monte_kPa == pytest.approx(0.0)


def test_golden_report_ok_and_has_nineteen_checks():
    report = run_muro_sostegno(TRATTO_A_INPUT)
    assert report.ok is True
    assert len(report.checks) == 19  # 8 combinazioni x (ribaltamento + scorrimento)


def test_golden_armatura_paramento_row151():
    armatura = run_muro_sostegno(TRATTO_A_INPUT).data.armatura_paramento
    assert armatura.combo_governante == "SISMA_1"
    assert armatura.as_nec_cm2_m == pytest.approx(2.3726, rel=1e-4)
    assert armatura.callout == "1φ8/20"


def test_golden_armatura_fondazione_valle_row169():
    armatura = run_muro_sostegno(TRATTO_A_INPUT).data.armatura_fondazione_valle
    assert armatura.combo_governante == "SISMA_1"
    assert armatura.as_nec_cm2_m == pytest.approx(0.387055, rel=1e-4)
    assert armatura.callout == "1φ4/20"


def test_golden_armatura_fondazione_monte_row187():
    armatura = run_muro_sostegno(TRATTO_A_INPUT).data.armatura_fondazione_monte
    assert armatura.combo_governante == "SISMA_1"
    assert armatura.as_nec_cm2_m == pytest.approx(2.89234, rel=1e-4)
    assert armatura.callout == "1φ10/20"

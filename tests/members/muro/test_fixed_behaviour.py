"""Fixed-behaviour tests (legacy_compat=False) for the muro-sostegno divergences, plus validation
boundaries. See docs/divergences/muro-sostegno.md."""
import pytest
from pydantic import ValidationError

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import run_muro_sostegno
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

BASE_KWARGS = {
    "gamma_terr_sat_kN_m3": 19.7,
    "gamma_terr_secco_kN_m3": 15.6,
    "phi_deg": 30.69,
    "delta_deg": 0,
    "beta_deg": 0,
    "psi_deg": 90,
    "omega_deg": 0,
    "ag_g": 0.136,
    "f0": 2.419,
    "categoria_sottosuolo": "C",
    "categoria_topografica": "T1",
    "beta_m": 0.24,
    "gamma_e": 1.0,
    "gamma_cls_kN_m3": 25,
    "s_base_m": 0.49,
    "s_top_m": 0.25,
    "s_fond_m": 0.3,
    "h_muro_m": 2.4,
    "b_valle_m": 0.26,
    "b_monte_m": 1.15,
    "q_kN_m2": 2,
    "copertura_paramento_m": 0.06,
    "grado_acciaio": "B450C",
    "passo_arm_paramento_m": 0.2,
    "copertura_fondazione_m": 0.06,
    "passo_arm_fondazione_m": 0.2,
}


def _combo(sequence, nome):
    return next(c for c in sequence if c.nome == nome)


def test_m1_static_combos_are_legacy_compat_invariant():
    """STR_1/STR_2 use γφ,terr=1 (Tab. 6.2.II M1): atan(tan(x)/1) == x, so the angoli_progetto
    divergence is a no-op and both modes match (Tools 1-3 have no other numeric divergence)."""
    legacy = run_muro_sostegno(MuroSostegnoInput(**BASE_KWARGS, legacy_compat=True)).data
    fixed = run_muro_sostegno(MuroSostegnoInput(**BASE_KWARGS, legacy_compat=False)).data
    for nome in ("STR_1", "STR_2"):
        assert _combo(legacy.spinte, nome).w_terr_kN == pytest.approx(_combo(fixed.spinte, nome).w_terr_kN)
        assert _combo(legacy.ribaltamento_scorrimento, nome).or_ribaltamento == pytest.approx(
            _combo(fixed.ribaltamento_scorrimento, nome).or_ribaltamento
        )
        assert _combo(legacy.ribaltamento_scorrimento, nome).verifica_ribaltamento.passed == _combo(
            fixed.ribaltamento_scorrimento, nome
        ).verifica_ribaltamento.passed


def test_m2_and_seismic_combos_diverge_from_legacy_compat():
    """GEO/EQU (γφ,terr=1.25, M2) diverge because of the φ'd/δd fix (angoli_progetto.py): the sheet's
    angle division under-reduces φ'd relative to NTC2018 Tab. 6.2.II (e.g. φ'k=30 -> sheet 24.00° vs.
    Tab. 6.2.II 24.79°), so the fixed φ'd is LARGER and Ka is SMALLER than the sheet's own (the
    sheet is the more conservative, if non-normative, of the two here). SISMA additionally diverges
    because of the added inertia forces (Fh, (1±kv) weight scaling) and the γR thresholds (tool.py),
    which push the fixed mode's seismic demand up, never down."""
    legacy = run_muro_sostegno(MuroSostegnoInput(**BASE_KWARGS, legacy_compat=True)).data
    fixed = run_muro_sostegno(MuroSostegnoInput(**BASE_KWARGS, legacy_compat=False)).data
    for nome in ("GEO_1", "GEO_2", "EQU_1", "EQU_2"):
        assert _combo(fixed.spinte, nome).phi_d_rad > _combo(legacy.spinte, nome).phi_d_rad
        assert _combo(fixed.spinte, nome).ka < _combo(legacy.spinte, nome).ka

    for nome in ("SISMA_1", "SISMA_2"):
        assert _combo(fixed.ribaltamento_scorrimento, nome).r_tot_kN > _combo(legacy.ribaltamento_scorrimento, nome).r_tot_kN
        assert _combo(fixed.ribaltamento_scorrimento, nome).m_rib_kNm > _combo(legacy.ribaltamento_scorrimento, nome).m_rib_kNm
        assert _combo(fixed.ribaltamento_scorrimento, nome).fh_kN > 0
        assert _combo(legacy.ribaltamento_scorrimento, nome).fh_kN == 0

    # γR thresholds: a static combination whose sheet OR/OS just clears 1.0 can now fail at γR>1.
    str1_fixed = _combo(fixed.ribaltamento_scorrimento, "STR_1")
    assert str1_fixed.verifica_scorrimento.limit == pytest.approx(1.1)
    assert str1_fixed.verifica_ribaltamento.limit == pytest.approx(1.15)
    sisma1_fixed = _combo(fixed.ribaltamento_scorrimento, "SISMA_1")
    assert sisma1_fixed.verifica_scorrimento.limit == pytest.approx(1.0)
    assert sisma1_fixed.verifica_ribaltamento.limit == pytest.approx(1.0)
    str1_legacy = _combo(legacy.ribaltamento_scorrimento, "STR_1")
    assert str1_legacy.verifica_scorrimento.limit == pytest.approx(1.0)
    assert str1_legacy.verifica_ribaltamento.limit == pytest.approx(1.0)


def test_bearing_capacity_warning_is_always_present():
    """Finding: capacità portante (NTC2018 §6.5.3.1.1) is out of this tool's scope; the report must
    say so explicitly instead of letting an all-green check list be read as a complete verification."""
    report = run_muro_sostegno(MuroSostegnoInput(**BASE_KWARGS, legacy_compat=False))
    assert any("capacità portante" in w for w in report.warnings)


def test_beta_greater_than_phi_deg_still_produces_a_valid_ka():
    """β > φd (steep slope) exercises the sheet's else-branch (Ka=U/V) without raising. `b_monte_m`
    is widened relative to `BASE_KWARGS` so the extra seismic demand (Fh, (1±kv) weights) added for
    `legacy_compat=False` does not push SISMA_1's eccentricity outside the footing here."""
    inputs = MuroSostegnoInput(**{**BASE_KWARGS, "phi_deg": 25.0, "beta_deg": 22.0, "b_monte_m": 1.6}, legacy_compat=False)
    data = run_muro_sostegno(inputs).data
    geo1 = _combo(data.spinte, "GEO_1")  # gamma_phi_terr=1.25 -> phi_d = atan(tan(25)/1.25) < beta = 22 deg
    str1 = _combo(data.spinte, "STR_1")  # gamma_phi_terr=1.0 -> phi_d = 25 deg > beta = 22 deg
    assert geo1.ka > 0
    assert str1.ka > 0
    assert geo1.ka != pytest.approx(str1.ka)


@pytest.mark.parametrize("field", ["phi_deg", "gamma_cls_kN_m3", "h_muro_m", "s_base_m"])
def test_non_positive_dimensional_inputs_are_rejected(field):
    with pytest.raises(ValidationError):
        MuroSostegnoInput(**{**BASE_KWARGS, field: 0.0})


def test_unknown_categoria_sottosuolo_is_rejected():
    with pytest.raises(ValidationError):
        MuroSostegnoInput(**{**BASE_KWARGS, "categoria_sottosuolo": "Z"})


def test_default_legacy_compat_is_false():
    assert MuroSostegnoInput(**BASE_KWARGS).legacy_compat is False


def test_eccentricity_beyond_half_width_raises_calc_error():
    """Resultant entirely outside the footing (|e| > B/2): the linear pressure formulas are not
    physically meaningful, so the tool raises CalcError instead of returning garbage numbers."""
    inputs = MuroSostegnoInput(**{**BASE_KWARGS, "q_kN_m2": 15.0, "b_monte_m": 0.4}, legacy_compat=False)
    with pytest.raises(CalcError):
        run_muro_sostegno(inputs)

import pytest

from strutture.loads.sisma.spettro_elastico import se_elastico

TB, TC, TD = 0.129398, 0.388193, 1.992
AG, S, F0, ETA = 0.098, 1.2, 2.436, 1.0


@pytest.mark.unit
def test_branch_1_ramp_at_zero():
    assert se_elastico(0, TB, TC, TD, AG, S, F0, ETA, legacy_compat=True) == pytest.approx(AG * S, rel=1e-6)
    assert se_elastico(0, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False) == pytest.approx(AG * S, rel=1e-6)


@pytest.mark.unit
def test_branch_2_plateau_is_continuous_with_branch_1_at_tb():
    just_below = se_elastico(TB - 1e-9, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False)
    at_tb = se_elastico(TB, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False)
    assert at_tb == pytest.approx(just_below, rel=1e-5)
    assert at_tb == pytest.approx(ETA * AG * S * F0, rel=1e-6)


@pytest.mark.unit
def test_branch_3_decays_as_tc_over_t():
    assert se_elastico(TC, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False) == pytest.approx(ETA * AG * S * F0, rel=1e-6)
    assert se_elastico(2 * TC, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False) == pytest.approx(ETA * AG * S * F0 * 0.5, rel=1e-6)


@pytest.mark.unit
def test_branch_4_decays_as_one_over_t_squared():
    at_td = se_elastico(TD, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False)
    at_double_td = se_elastico(2 * TD, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False)
    assert at_double_td == pytest.approx(at_td / 4, rel=1e-6)


@pytest.mark.unit
def test_negative_period_rejected():
    with pytest.raises(ValueError):
        se_elastico(-1, TB, TC, TD, AG, S, F0, ETA, legacy_compat=False)


@pytest.mark.unit
def test_fixed_t_zero_anchors_to_ag_s_regardless_of_eta():
    """NTC2018 eq. 3.2.4: Se(0) = ag*S always (PGA anchoring), for any damping eta, since the
    reciprocal term 1/(eta*F0) carries eta, cancelling it out at T=0."""
    eta_10_pct_damping = (10.0 / (5.0 + 10.0)) ** 0.5  # xi=10% -> eta=0.816...
    assert eta_10_pct_damping != pytest.approx(1.0)
    assert se_elastico(0, TB, TC, TD, AG, S, F0, eta_10_pct_damping, legacy_compat=False) == pytest.approx(AG * S, rel=1e-6)


@pytest.mark.unit
def test_fixed_branch_1_interior_point_carries_eta_in_the_reciprocal_term():
    eta = 0.816497  # xi=10%
    t_s = TB / 2
    expected = eta * AG * S * F0 * (t_s / TB + (1.0 / (eta * F0)) * (1.0 - t_s / TB))
    assert se_elastico(t_s, TB, TC, TD, AG, S, F0, eta, legacy_compat=False) == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
def test_legacy_t_zero_reproduces_sheet_bug_dropping_eta_at_high_damping():
    """Sisma!N56:N149 bug: the reciprocal term is (1/F0), not (1/(eta*F0)) -- so legacy Se(0) is
    eta*ag*S, not ag*S, for eta != 1 (confirmed against tests/fixtures/sisma_spettro_oracle.json
    case 2, xi=8%)."""
    eta = 0.816497  # xi=10%
    assert se_elastico(0, TB, TC, TD, AG, S, F0, eta, legacy_compat=True) == pytest.approx(eta * AG * S, rel=1e-6)

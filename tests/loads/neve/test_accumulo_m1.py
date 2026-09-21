import pytest

from strutture.loads.neve.accumulo_m1 import m1_finale, m1_interpolato


@pytest.mark.unit
def test_b2_at_or_above_ls_returns_manual_input_unchanged():
    assert m1_finale(20, 15, mu_w=4, m1_input=0.8, legacy_compat=False) == pytest.approx(0.8)
    assert m1_finale(15, 15, mu_w=4, m1_input=0.8, legacy_compat=False) == pytest.approx(0.8)


@pytest.mark.unit
def test_b2_below_ls_interpolates_between_mw_and_m1():
    # ls=15, b2=0 -> the far-edge value equals mw itself (within the [0, 4] clamp range)
    assert m1_interpolato(0, 15, mu_w=1.5, m1_input=0.8, legacy_compat=False) == pytest.approx(1.5)
    # b2=ls -> equals the manual input
    assert m1_interpolato(15, 15, mu_w=1.5, m1_input=0.8, legacy_compat=False) == pytest.approx(0.8)


@pytest.mark.unit
def test_bug_7_extrapolation_beyond_ls_is_clamped_only_in_fixed_mode():
    """`docs/specs/neve.md` §7.7 / architecture.md §6: extrapolating past `ls` (b2 > ls) can drive
    the interpolated value far outside [0, 2]; legacy mode reproduces the raw (unclamped) sheet
    value (confirmed against the spec §8 golden case: b2=36.2 > ls=15 -> M38=-3.67673), fixed mode
    clamps to [0, 2].
    """
    legacy = m1_interpolato(36.2, 15, mu_w=3.9675, m1_input=0.8, legacy_compat=True)
    fixed = m1_interpolato(36.2, 15, mu_w=3.9675, m1_input=0.8, legacy_compat=False)
    assert legacy == pytest.approx(-3.67673, rel=1e-5)
    assert fixed == pytest.approx(0.0)  # clamped up from the negative raw value


@pytest.mark.unit
def test_bug_7_clamp_upper_bound():
    # mw=4 (its own cap), m1_input=5 (implausibly large manual input), b2 close to ls -> raw > 4
    legacy = m1_interpolato(14, 15, mu_w=4, m1_input=5, legacy_compat=True)
    fixed = m1_interpolato(14, 15, mu_w=4, m1_input=5, legacy_compat=False)
    assert legacy > 4
    assert fixed == pytest.approx(4.0)


@pytest.mark.unit
def test_no_spurious_2_0_cap_legitimate_values_above_2_pass_through():
    """Reviewed finding (CRITICAL): the old `M1_INTERP_MAX = 2.0` had no basis in Circ. §C3.4.5.6
    / EN1991-1-3 §6.2 — the only limit on the drift shape coefficient is 0.8 <= mu_w <= 4
    (`accumulo_mw.MW_MAX`). A legitimate interpolated value in (2, 4] must not be truncated.
    Example from the finding: h=8 m, b1=40 m, b2=1 m, ls=15 m, mu_w=2.5625 (=min((40+1)/16,
    2*8/1.5)), m1_input=0.8 -> interpolated=2.445, which must pass through unclamped in fixed
    mode (previously silently truncated to 2.0, a ~18% reduction).
    """
    fixed = m1_interpolato(1, 15, mu_w=2.5625, m1_input=0.8, legacy_compat=False)
    assert fixed == pytest.approx(2.445, rel=1e-6)
    assert fixed > 2.0

import pytest

from strutture.loads.sisma.spettro_progetto import DESIGN_SPECTRUM_FLOOR_RATIO, valore_spettro

# Shared fixed-branch geometry for tests below: TB=0.129398, S=1.2, F0=2.436 (spec §8 golden case).
TB, S, F0 = 0.129398, 1.2, 2.436


@pytest.mark.unit
def test_sle_states_pass_se_through_unreduced():
    assert valore_spettro(0.5, 1.5, 1.0, is_uls=False, ag_g=0.1, s=S, f0=F0, tb_s=TB, legacy_compat=True) == pytest.approx(0.5)
    assert valore_spettro(0.5, 1.5, 1.0, is_uls=False, ag_g=0.1, s=S, f0=F0, tb_s=TB, legacy_compat=False) == pytest.approx(0.5)


@pytest.mark.unit
def test_uls_divides_by_q():
    assert valore_spettro(0.3, 1.5, 1.0, is_uls=True, ag_g=0.05, s=S, f0=F0, tb_s=TB, legacy_compat=True) == pytest.approx(0.2)


@pytest.mark.unit
def test_legacy_t_zero_skips_the_division_sheet_bug():
    """Sisma!J55 = `=N55` (no IF/division), unlike every other row."""
    assert valore_spettro(0.3, 1.5, 0.0, is_uls=True, ag_g=0.05, s=S, f0=F0, tb_s=TB, legacy_compat=True) == pytest.approx(0.3)


@pytest.mark.unit
def test_fixed_does_not_divide_by_q_at_t_zero():
    """NTC18 §3.2.3.5: Sd(0) = ag*S exactly (PGA anchoring under the eta->1/q substitution), not
    Se(0)/q. The sheet's undivided T=0 value (Sisma!J55) was code-compliant, not a bug."""
    ag_g = 0.098
    se_at_zero = ag_g * S  # Se(0) = ag*S regardless of eta (see test_spettro_elastico)
    result = valore_spettro(se_at_zero, 1.5, 0.0, is_uls=True, ag_g=ag_g, s=S, f0=F0, tb_s=TB, legacy_compat=False)
    assert result == pytest.approx(ag_g * S, rel=1e-6)


@pytest.mark.unit
def test_fixed_short_period_branch_uses_eta_to_1_over_q_substitution():
    """0<=T<TB: Sd(T) = ag*S*F0/q*(T/TB) + ag*S*(1-T/TB), NOT Se(T)/q (NTC18 eq. 3.2.4 with
    eta replaced by 1/q, per §3.2.3.5)."""
    ag_g, q = 0.098, 1.5
    t_s = TB / 2
    se_g = 1.0 * ag_g * S * F0 * (t_s / TB + (1.0 / F0) * (1.0 - t_s / TB))  # Se(T) at eta=1, for contrast
    expected = ag_g * S * F0 / q * (t_s / TB) + ag_g * S * (1.0 - t_s / TB)
    result = valore_spettro(se_g, q, t_s, is_uls=True, ag_g=ag_g, s=S, f0=F0, tb_s=TB, legacy_compat=False)
    assert result == pytest.approx(expected, rel=1e-6)
    assert result != pytest.approx(se_g / q, rel=1e-3)


@pytest.mark.unit
def test_fixed_applies_0_2ag_floor():
    # se/q = 0.001/1.5 = 0.000667, well below 0.2*ag = 0.02 -- at T=3 >= TB, on the Se/q branch
    result = valore_spettro(0.001, 1.5, 3.0, is_uls=True, ag_g=0.1, s=S, f0=F0, tb_s=TB, legacy_compat=False)
    assert result == pytest.approx(DESIGN_SPECTRUM_FLOOR_RATIO * 0.1)


@pytest.mark.unit
def test_legacy_does_not_apply_the_floor():
    result = valore_spettro(0.001, 1.5, 3.0, is_uls=True, ag_g=0.1, s=S, f0=F0, tb_s=TB, legacy_compat=True)
    assert result == pytest.approx(0.001 / 1.5)

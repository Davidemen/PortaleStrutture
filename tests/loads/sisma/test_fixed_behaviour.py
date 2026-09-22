"""Fixed-behaviour tests (`legacy_compat=False`) for every divergence in `docs/divergences/sisma.md`."""
import pytest

from strutture.loads.sisma.eta_verticale import eta_verticale
from strutture.loads.sisma.smorzamento import smorzamento_eta
from strutture.loads.sisma.spettro_elastico import se_elastico
from strutture.loads.sisma.spettro_progetto import valore_spettro


@pytest.mark.unit
def test_vertical_eta_uses_damping_formula_not_1_over_qv():
    """Sisma!I45 bug: `=1/I44`. Fixed: same η(ξ) formula as the horizontal component."""
    xi_pct, qv = 5.0, 1.5
    fixed = eta_verticale(xi_pct, qv, legacy_compat=False)
    legacy = eta_verticale(xi_pct, qv, legacy_compat=True)
    assert legacy == pytest.approx(1 / qv, rel=1e-9)
    assert fixed == pytest.approx(smorzamento_eta(xi_pct), rel=1e-9)
    assert fixed != pytest.approx(legacy, rel=1e-3)


@pytest.mark.unit
def test_design_spectrum_gets_0_2ag_floor_at_long_periods():
    """NTC2018 §3.2.3.2.1: Sd(T) >= 0.2·ag. The sheet has no such floor."""
    tb, tc, td = 0.129398, 0.388193, 1.992
    ag_g, s, f0, eta, q = 0.098, 1.2, 2.436, 1.0, 1.5
    t_s = 5.0
    se_g = se_elastico(t_s, tb, tc, td, ag_g, s, f0, eta, legacy_compat=True)

    legacy = valore_spettro(se_g, q, t_s, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=True)
    fixed = valore_spettro(se_g, q, t_s, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=False)

    assert legacy == pytest.approx(0.00590732, rel=1e-5)  # spec §8 golden value, unfloored
    assert fixed == pytest.approx(0.2 * ag_g, rel=1e-9)  # floored
    assert fixed > legacy


@pytest.mark.unit
def test_floor_does_not_bind_where_sheet_value_already_exceeds_it():
    tb, tc, td = 0.129398, 0.388193, 1.992
    ag_g, s, f0, eta, q = 0.098, 1.2, 2.436, 1.0, 1.5
    se_g = se_elastico(td, tb, tc, td, ag_g, s, f0, eta, legacy_compat=True)
    assert valore_spettro(se_g, q, td, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=False) == pytest.approx(
        valore_spettro(se_g, q, td, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=True), rel=1e-9
    )


@pytest.mark.unit
def test_t_zero_design_value_is_not_divided_by_q_even_when_fixed():
    """Sisma!J55 (`=N55`, no SLU division) is code-compliant, not a bug: NTC18 §3.2.3.5 anchors
    Sd(0) = ag*S exactly for any q (eta->1/q substitution cancels out at T=0). Both legacy and
    fixed modes agree here."""
    tb, tc, td = 0.129398, 0.388193, 1.992
    ag_g, s, f0, eta, q = 0.098, 1.2, 2.436, 1.0, 1.5
    se_g = se_elastico(0.0, tb, tc, td, ag_g, s, f0, eta, legacy_compat=True)

    legacy = valore_spettro(se_g, q, 0.0, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=True)
    fixed = valore_spettro(se_g, q, 0.0, is_uls=True, ag_g=ag_g, s=s, f0=f0, tb_s=tb, eta=1.0, legacy_compat=False)

    assert legacy == pytest.approx(0.1176, rel=1e-5)  # spec §8 golden value, undivided
    assert fixed == pytest.approx(0.1176, rel=1e-5)  # NTC-compliant: also undivided at T=0

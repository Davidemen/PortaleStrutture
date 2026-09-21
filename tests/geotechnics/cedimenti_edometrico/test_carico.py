"""Unit tests for `pressione_netta` (q' = q − γ·D; docs/architecture-batch2.md §7 review finding
HIGH/`righe.py`: the relief must use the same effective-weight/water-table basis as σ'v0, and
q' <= 0 must fail fast instead of propagating a negative settlement)."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.carico import pressione_netta
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_zero_embedment_leaves_q_unchanged() -> None:
    result = pressione_netta(q_kPa=49.03325, gamma_kN_m3=17.65197, d_m=0.0)
    assert result.sovraccarico_rimosso_kPa == pytest.approx(0.0)
    assert result.q_prime_kPa == pytest.approx(49.03325)


@pytest.mark.unit
def test_embedment_reduces_net_pressure() -> None:
    result = pressione_netta(q_kPa=100.0, gamma_kN_m3=18.0, d_m=1.0)
    assert result.sovraccarico_rimosso_kPa == pytest.approx(18.0)
    assert result.q_prime_kPa == pytest.approx(82.0)


@pytest.mark.unit
def test_q_is_echoed_unchanged() -> None:
    result = pressione_netta(q_kPa=100.0, gamma_kN_m3=18.0, d_m=1.0)
    assert result.q_kPa == pytest.approx(100.0)


@pytest.mark.unit
def test_legacy_compat_ignores_the_water_table_even_when_given() -> None:
    """The sheet's own `q'=q−γ·D` formula never had a water table; `legacy_compat=True` must stay
    byte-identical regardless of `water_table_m` (docs/architecture-batch2.md §9-D1 "legacy stays
    frozen")."""
    result = pressione_netta(q_kPa=100.0, gamma_kN_m3=18.0, d_m=1.0, water_table_m=0.2, legacy_compat=True)
    assert result.sovraccarico_rimosso_kPa == pytest.approx(18.0)
    assert result.q_prime_kPa == pytest.approx(82.0)


@pytest.mark.unit
def test_standard_mode_without_a_water_table_matches_the_legacy_formula() -> None:
    """No `water_table_m` given (dry site assumption) => plain total weight, same number as
    `legacy_compat=True` — only an explicit water table changes the standard-mode relief."""
    result = pressione_netta(q_kPa=100.0, gamma_kN_m3=18.0, d_m=1.0, legacy_compat=False)
    assert result.sovraccarico_rimosso_kPa == pytest.approx(18.0)
    assert result.q_prime_kPa == pytest.approx(82.0)


@pytest.mark.unit
def test_standard_mode_applies_buoyant_weight_below_an_explicit_water_table() -> None:
    """Water table at the ground surface (`water_table_m=0.0`): the whole embedment is submerged,
    so the relief uses the buoyant unit weight, not the total one."""
    result = pressione_netta(q_kPa=100.0, gamma_kN_m3=18.0, d_m=1.0, water_table_m=0.0, legacy_compat=False)
    assert result.sovraccarico_rimosso_kPa == pytest.approx(18.0 - 9.80665)
    assert result.q_prime_kPa == pytest.approx(100.0 - (18.0 - 9.80665))


@pytest.mark.unit
def test_deep_embedment_raises_calc_error_instead_of_a_negative_net_pressure() -> None:
    """`d` accepts up to 200 m (models.py); a deep enough embedment must fail loudly, naming
    q/γ/D, instead of handing a negative q' downstream (docs/architecture-batch2.md §7 review
    finding MEDIUM/`carico.py`)."""
    with pytest.raises(CalcError, match=r"q'"):
        pressione_netta(q_kPa=50.0, gamma_kN_m3=18.0, d_m=10.0)


@pytest.mark.unit
def test_zero_net_pressure_also_raises() -> None:
    with pytest.raises(CalcError):
        pressione_netta(q_kPa=18.0, gamma_kN_m3=18.0, d_m=1.0)

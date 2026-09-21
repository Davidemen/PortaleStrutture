import pytest

from strutture.loads.neve.forma_falda import coefficiente_forma


@pytest.mark.unit
def test_parapetto_forces_flat_value_regardless_of_angle():
    assert coefficiente_forma(80, True, legacy_compat=False) == pytest.approx(0.8)
    assert coefficiente_forma(80, True, legacy_compat=True) == pytest.approx(0.8)


@pytest.mark.unit
@pytest.mark.parametrize("legacy_compat", [False, True])
def test_below_30_degrees_is_flat(legacy_compat: bool):
    assert coefficiente_forma(29.999, False, legacy_compat=legacy_compat) == pytest.approx(0.8)


@pytest.mark.unit
@pytest.mark.parametrize("legacy_compat", [False, True])
def test_above_60_degrees_is_zero(legacy_compat: bool):
    assert coefficiente_forma(60.001, False, legacy_compat=legacy_compat) == pytest.approx(0.0)


@pytest.mark.unit
def test_boundary_at_30_degrees_bug_6():
    """Fixed mode: 30° is the ramp's start (continuous with 0.8 just below). Legacy mode: the
    sheet's strict `AND(a>30, a<60)` drops exactly 30° to the else branch -> 0 (discontinuity).
    """
    assert coefficiente_forma(30, False, legacy_compat=False) == pytest.approx(0.8)
    assert coefficiente_forma(30, False, legacy_compat=True) == pytest.approx(0.0)


@pytest.mark.unit
def test_boundary_at_60_degrees_matches_in_both_modes():
    """At exactly 60° both modes fall through to 0 — the ramp's own formula already evaluates to
    0 there, so the strict-vs-inclusive upper bound makes no numeric difference.
    """
    assert coefficiente_forma(60, False, legacy_compat=False) == pytest.approx(0.0)
    assert coefficiente_forma(60, False, legacy_compat=True) == pytest.approx(0.0)


@pytest.mark.unit
def test_ramp_midpoint():
    assert coefficiente_forma(45, False, legacy_compat=False) == pytest.approx(0.4)

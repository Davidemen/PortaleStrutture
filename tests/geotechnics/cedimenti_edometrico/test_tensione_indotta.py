"""Unit tests for `tensione_indotta` (Δσv,q approssimato vs Newmark, `metodo_tensioni` selection)."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.tensione_indotta import tensione_indotta
from strutture.shared.soil_stress import spread_2to1, under_center


@pytest.mark.unit
def test_at_z_zero_both_equal_q_prime_and_newmark_is_none() -> None:
    result = tensione_indotta(49.03325, 3.5, 5.0, 0.0, metodo="newmark")
    assert result.approssimato_kPa == pytest.approx(49.03325)
    assert result.newmark_kPa is None
    assert result.utilizzato_kPa == pytest.approx(49.03325)


@pytest.mark.unit
def test_approssimato_matches_spread_2to1() -> None:
    result = tensione_indotta(49.03325, 3.5, 5.0, 2.0, metodo="approssimato")
    assert result.approssimato_kPa == pytest.approx(spread_2to1(49.03325, 3.5, 5.0, 2.0))
    assert result.utilizzato_kPa == pytest.approx(result.approssimato_kPa)


@pytest.mark.unit
def test_newmark_matches_under_center_and_is_used_when_selected() -> None:
    result = tensione_indotta(49.03325, 3.5, 5.0, 2.0, metodo="newmark")
    assert result.newmark_kPa == pytest.approx(under_center(49.03325, 3.5, 5.0, 2.0))
    assert result.utilizzato_kPa == pytest.approx(result.newmark_kPa)


@pytest.mark.unit
def test_approssimato_and_newmark_differ_away_from_the_surface() -> None:
    """The sheet's spread formula is only an approximation of the exact Newmark integral —
    the two methods diverge at depth (docs/architecture-batch2.md §1.1)."""
    result = tensione_indotta(49.03325, 3.5, 5.0, 5.0, metodo="newmark")
    assert result.approssimato_kPa != pytest.approx(result.newmark_kPa, rel=1e-3)

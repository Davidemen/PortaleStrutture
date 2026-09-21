"""Rule 4 (units never guessed): explicit factor tables, case-insensitive, unknown unit is an
error — docs/integrations/MIDAS.md."""
import pytest

from strutture.integrations.midas import moment_factor, to_kn, to_m


@pytest.mark.unit
@pytest.mark.parametrize(("value", "unit", "expected"), [(1000.0, "N", 1.0), (1.0, "kn", 1.0), (1.0, "KGF", 0.00980665)])
def test_to_kn(value: float, unit: str, expected: float) -> None:
    assert to_kn(value, unit) == pytest.approx(expected)


@pytest.mark.unit
@pytest.mark.parametrize(("value", "unit", "expected"), [(1000.0, "MM", 1.0), (1.0, "m", 1.0), (1.0, "FT", 0.3048)])
def test_to_m(value: float, unit: str, expected: float) -> None:
    assert to_m(value, unit) == pytest.approx(expected)


@pytest.mark.unit
def test_moment_factor_n_mm_to_kn_m() -> None:
    # 1 N*mm = 1e-3 kN * 1e-3 m = 1e-6 kN*m
    assert moment_factor("N", "MM") == pytest.approx(1e-6)


@pytest.mark.unit
def test_unknown_force_unit_raises() -> None:
    with pytest.raises(ValueError):
        to_kn(1.0, "STONES")


@pytest.mark.unit
def test_unknown_length_unit_raises() -> None:
    with pytest.raises(ValueError):
        to_m(1.0, "LEAGUES")


@pytest.mark.unit
def test_unknown_unit_in_moment_factor_raises() -> None:
    with pytest.raises(ValueError):
        moment_factor("N", "LEAGUES")

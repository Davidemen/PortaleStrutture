"""`steinbrenner_is` against the Timoshenko-Goodier sheet's golden case
(`docs/specs/geo-cedimenti-elastico.md` Tool 2 golden test case: B=L=100cm, D=50cm, μ=0.35,
H=500cm -> a=L/B=1, b_centro=2H/B=10, b_bordo=H/B=5)."""
import pytest

from strutture.shared.soil_stress import steinbrenner_is


@pytest.mark.golden
def test_is_centro_matches_sheet_n15() -> None:
    assert steinbrenner_is(1.0, 10.0, 0.35) == pytest.approx(0.505131, rel=1e-5)


@pytest.mark.golden
def test_is_bordo_matches_sheet_p15() -> None:
    assert steinbrenner_is(1.0, 5.0, 0.35) == pytest.approx(0.451165, rel=1e-5)


@pytest.mark.unit
@pytest.mark.parametrize("mu", [-0.1, 0.5, 0.6])
def test_rejects_poisson_ratio_out_of_range(mu: float) -> None:
    with pytest.raises(ValueError, match="mu"):
        steinbrenner_is(1.0, 1.0, mu)


@pytest.mark.unit
@pytest.mark.parametrize("m,n", [(0.0, 1.0), (1.0, 0.0), (-1.0, 1.0)])
def test_rejects_non_positive_ratios(m: float, n: float) -> None:
    with pytest.raises(ValueError, match="m, n"):
        steinbrenner_is(m, n, 0.3)

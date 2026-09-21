"""buckling_curve.py — Tab. 6.1/6.2/6.3 curve selection (docs/architecture.md §6, column-check Y25/Y26/BC17)."""
import pytest

from strutture.members.acciaio_colonna_ec3.buckling_curve import (
    alpha_flessionali,
    alpha_lt,
    curva_lt,
    curve_flessionali_tab_6_2,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "h_mm,b_mm,lavorazione,atteso",
    [(500, 280, "hot finished", "b"), (600, 280, "hot finished", "c"), (500, 280, "cold formed", "c"), (600, 280, "cold formed", "d")],
)
def test_curva_lt_matches_column_check_bc17(h_mm: float, b_mm: float, lavorazione: str, atteso: str) -> None:
    assert curva_lt(h_mm, b_mm, lavorazione) == atteso  # type: ignore[arg-type]


@pytest.mark.unit
def test_alpha_lt_table_6_1() -> None:
    assert alpha_lt("a") == 0.21
    assert alpha_lt("b") == 0.34
    assert alpha_lt("c") == 0.49
    assert alpha_lt("d") == 0.76


@pytest.mark.unit
@pytest.mark.parametrize(
    "h_mm,b_mm,tf_mm,atteso",
    [
        (500, 280, 12, ("a", "b")),  # h/b>1.2, tf<=40
        (500, 280, 60, ("b", "c")),  # h/b>1.2, 40<tf<=100
        (500, 280, 120, ("d", "d")),  # h/b>1.2, tf>100
        (500, 450, 60, ("b", "c")),  # h/b<=1.2, tf<=100
        (500, 450, 120, ("d", "d")),  # h/b<=1.2, tf>100
    ],
)
def test_curve_flessionali_tab_6_2(h_mm: float, b_mm: float, tf_mm: float, atteso: tuple[str, str]) -> None:
    assert curve_flessionali_tab_6_2(h_mm, b_mm, tf_mm) == atteso


@pytest.mark.unit
def test_legacy_reproduces_hardcoded_hot_cold_pairs_bypassing_the_curve() -> None:
    """docs/architecture.md §6 acciaio Y25/Y26: sheet ignores the curve letter entirely."""
    alpha_yy, alpha_zz, _, _ = alpha_flessionali(500, 280, 12, "hot finished", legacy_compat=True)
    assert (alpha_yy, alpha_zz) == (0.34, 0.49)
    alpha_yy_cold, alpha_zz_cold, _, _ = alpha_flessionali(500, 280, 12, "cold formed", legacy_compat=True)
    assert (alpha_yy_cold, alpha_zz_cold) == (0.21, 0.34)


@pytest.mark.unit
def test_fixed_derives_alpha_from_tab_6_2_curve_per_axis() -> None:
    """Fixed behaviour: h/b=500/280>1.2, tf=12<=40 -> curve a (yy)/b (zz), NOT the legacy 0.34/0.49 pair."""
    alpha_yy, alpha_zz, curva_yy, curva_zz = alpha_flessionali(500, 280, 12, "hot finished", legacy_compat=False)
    assert (curva_yy, curva_zz) == ("a", "b")
    assert (alpha_yy, alpha_zz) == (0.21, 0.34)

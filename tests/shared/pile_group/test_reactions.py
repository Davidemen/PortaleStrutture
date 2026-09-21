"""docs/specs/fond-plinti-pali.md Tool 1, row "SLU4": final pile-head loads N=1899.96 kN,
Mx,final=11.0284 kNm, My,final=-188.942 kNm on a 2x2 grid (Lx=Ly=2 m, §AR21/AR22 defaults)
give Nmin,pile=424.997 kN / Nmax,pile=524.982 kN — the sheet's simplified Case-1 formula, which for
a symmetric 2x2 grid is algebraically identical to the general `rigid_cap_axial` closed form
(Sigma x^2 = Sigma y^2 = spacing^2, so `M*e/2 / spacing^2 == M/(spacing*count_per_row)`)."""
import pytest

from strutture.shared.pile_group import pile_coordinates, rigid_cap_axial


def test_golden_2x2_pile_cap_matches_spec_row_slu4():
    piles = pile_coordinates("2x2", spacing_x_m=2.0, spacing_y_m=2.0)
    reactions = rigid_cap_axial(n_kN=1899.96, mx_kNm=11.0284, my_kNm=-188.942, piles=piles)
    assert max(reactions) == pytest.approx(524.982, rel=2e-4)
    assert min(reactions) == pytest.approx(424.997, rel=2e-4)


def test_no_moment_gives_equal_share():
    piles = pile_coordinates("2x2", spacing_x_m=2.0, spacing_y_m=2.0)
    reactions = rigid_cap_axial(n_kN=800.0, mx_kNm=0.0, my_kNm=0.0, piles=piles)
    assert reactions == (200.0, 200.0, 200.0, 200.0)


def test_single_pile_ignores_moments():
    piles = pile_coordinates("1x1", spacing_x_m=0.0, spacing_y_m=0.0)
    reactions = rigid_cap_axial(n_kN=500.0, mx_kNm=999.0, my_kNm=-999.0, piles=piles)
    assert reactions == (500.0,)


def test_collinear_piles_ignore_the_orthogonal_moment():
    # 2x1 grid: all piles have y=0, so Mx (which needs a y lever arm) contributes nothing.
    piles = pile_coordinates("2x1", spacing_x_m=2.0, spacing_y_m=0.0)
    reactions = rigid_cap_axial(n_kN=400.0, mx_kNm=123.0, my_kNm=0.0, piles=piles)
    assert reactions == (200.0, 200.0)


def test_arbitrary_asymmetric_coordinates():
    from strutture.shared.pile_group import PilePos

    piles = (PilePos(x_m=-1.0, y_m=0.5), PilePos(x_m=2.0, y_m=-1.0), PilePos(x_m=0.5, y_m=1.5))
    reactions = rigid_cap_axial(n_kN=300.0, mx_kNm=50.0, my_kNm=-20.0, piles=piles)
    sum_x2 = sum(p.x_m**2 for p in piles)
    sum_y2 = sum(p.y_m**2 for p in piles)
    expected = tuple(300.0 / 3 + 50.0 * p.y_m / sum_y2 + (-20.0) * p.x_m / sum_x2 for p in piles)
    assert reactions == pytest.approx(expected)


def test_zero_piles_rejected():
    with pytest.raises(ValueError):
        rigid_cap_axial(n_kN=100.0, mx_kNm=0.0, my_kNm=0.0, piles=())

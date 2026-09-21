import pytest

from strutture.shared.pile_group import PilePos, pile_coordinates


def test_2x2_grid_centred_at_origin():
    piles = pile_coordinates("2x2", spacing_x_m=2.0, spacing_y_m=2.0)
    assert {(p.x_m, p.y_m) for p in piles} == {(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)}


def test_2x1_grid():
    piles = pile_coordinates("2x1", spacing_x_m=3.0, spacing_y_m=0.0)
    assert {(p.x_m, p.y_m) for p in piles} == {(-1.5, 0.0), (1.5, 0.0)}


def test_1x2_grid():
    piles = pile_coordinates("1x2", spacing_x_m=0.0, spacing_y_m=4.0)
    assert {(p.x_m, p.y_m) for p in piles} == {(0.0, -2.0), (0.0, 2.0)}


def test_1x1_single_pile_at_centroid():
    piles = pile_coordinates("1x1", spacing_x_m=0.0, spacing_y_m=0.0)
    assert piles == (PilePos(x_m=0.0, y_m=0.0),)


def test_unknown_schema_rejected():
    with pytest.raises(KeyError):
        pile_coordinates("3x3", spacing_x_m=1.0, spacing_y_m=1.0)  # type: ignore[arg-type]


def test_centred_positions_rejects_non_positive_count():
    from strutture.shared.pile_group.pattern import _centred_positions

    with pytest.raises(ValueError):
        _centred_positions(0, 1.0)

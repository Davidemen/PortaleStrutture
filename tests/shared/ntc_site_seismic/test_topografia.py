"""Unit tests for fattore_topografico_st (NTC 2018 Tab. 3.2.V)."""
import pytest

from strutture.shared.ntc_site_seismic.topografia import fattore_topografico_st
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("categoria", "st"),
    [("T1", 1.0), ("T2", 1.2), ("T3", 1.2), ("T4", 1.4)],
)
def test_fattore_topografico_st_per_categoria(categoria, st):
    assert fattore_topografico_st(categoria) == pytest.approx(st)


def test_fattore_topografico_st_unknown_categoria_raises():
    with pytest.raises(KeyNotFound):
        fattore_topografico_st("T5")

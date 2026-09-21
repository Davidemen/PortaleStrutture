"""Unit tests for periodo_ritorno/periodi_ritorno (NTC 2018 §3.2.1 eq. 3.2.1)."""
import pytest

from strutture.shared.ntc_site_seismic.periodo_ritorno import periodi_ritorno, periodo_ritorno
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("stato_limite", "tr"),
    [("SLO", 30), ("SLD", 50), ("SLV", 475), ("SLC", 975)],
)
def test_periodo_ritorno_per_stato_limite(stato_limite, tr):
    assert periodo_ritorno(50, stato_limite) == pytest.approx(tr)


def test_periodo_ritorno_case_insensitive_stato_limite():
    # NTC18 dropdown values are uppercase; the sheet's own formula compares against lowercase
    # literals ("slv"/"slc") which only works because Excel text compares case-insensitively.
    assert periodo_ritorno(50, "slv") == pytest.approx(475)


def test_periodo_ritorno_unknown_stato_limite_raises():
    with pytest.raises(KeyNotFound):
        periodo_ritorno(50, "SLZ")


def test_periodi_ritorno_returns_all_four_states():
    result = periodi_ritorno(50)
    assert (result.slo, result.sld, result.slv, result.slc) == pytest.approx((30, 50, 475, 975))

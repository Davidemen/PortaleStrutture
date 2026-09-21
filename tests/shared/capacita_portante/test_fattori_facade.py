"""The `fattori.py` facade re-exports the same functions as the private per-factor modules."""
import pytest

from strutture.shared.capacita_portante import fattori

pytestmark = pytest.mark.unit


def test_facade_exposes_every_factor_function():
    portanza = fattori.fattori_portanza(30.0)
    m = fattori.esponente_m(2.0, 4.0, direzione="B")
    forma = fattori.fattori_forma(2.0, 4.0, 30.0, portanza.nq)
    carico = fattori.fattori_inclinazione_carico(0.0, 1000.0, 6.0, 0.0, 30.0, portanza.nc, m=m)
    base = fattori.fattori_inclinazione_base(0.0, 30.0, portanza.nc)
    assert portanza.nq > 1.0
    assert forma.sq > 1.0
    assert carico.iq == pytest.approx(1.0)
    assert base.bq == pytest.approx(1.0)
    assert fattori.fattori_forma_non_drenata(2.0, 4.0) > 1.0
    assert fattori.fattori_inclinazione_carico_non_drenata(0.0, 6.0, 50.0) == pytest.approx(1.0)
    assert fattori.fattori_inclinazione_base_non_drenata(0.0).bc == pytest.approx(1.0)

"""Unit tests for the NTC2018 Tab. 6.2.I/6.2.II/6.5.I lookups."""
import pytest

from strutture.shared.ntc_combos import fattori_azioni, fattori_geotecnici, fattori_resistenza
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("approccio", "favorevole", "sfavorevole"),
    [("EQU", 0.9, 1.1), ("A1", 1.0, 1.3), ("A2", 1.0, 1.0)],
)
def test_fattori_azioni_g1(approccio, favorevole, sfavorevole):
    result = fattori_azioni(approccio)
    assert result.gamma_g1_favorevole == pytest.approx(favorevole)
    assert result.gamma_g1_sfavorevole == pytest.approx(sfavorevole)


@pytest.mark.parametrize("approccio", ["EQU", "A1", "A2"])
def test_fattori_azioni_g2_favorevole_is_08(approccio):
    # NTC2018 Tab. 6.2.I: gamma_G2 favorevole = 0.8 in every column (raised from NTC2008's 0.0).
    assert fattori_azioni(approccio).gamma_g2_favorevole == pytest.approx(0.8)


def test_fattori_azioni_unknown_approccio_raises():
    with pytest.raises(KeyNotFound):
        fattori_azioni("A3")


@pytest.mark.parametrize(("approccio", "gamma_tan_phi"), [("M1", 1.0), ("M2", 1.25)])
def test_fattori_geotecnici_gamma_tan_phi(approccio, gamma_tan_phi):
    assert fattori_geotecnici(approccio).gamma_tan_phi == pytest.approx(gamma_tan_phi)


def test_fattori_geotecnici_unknown_approccio_raises():
    with pytest.raises(KeyNotFound):
        fattori_geotecnici("M3")


@pytest.mark.parametrize(
    ("verifica", "r3"),
    [("capacita_portante", 1.4), ("scorrimento", 1.1), ("resistenza_terreno_a_valle", 1.4)],
)
def test_fattori_resistenza_r3(verifica, r3):
    result = fattori_resistenza(verifica)
    assert result.r1 == pytest.approx(1.0)
    assert result.r2 == pytest.approx(1.0)
    assert result.r3 == pytest.approx(r3)


def test_fattori_resistenza_ribaltamento():
    # NTC2018 Tab. 6.5.I, "Ribaltamento" row: gamma_R = 1.0 / 1.15 / 1.15.
    result = fattori_resistenza("ribaltamento")
    assert result.r1 == pytest.approx(1.0)
    assert result.r2 == pytest.approx(1.15)
    assert result.r3 == pytest.approx(1.15)


def test_fattori_resistenza_unknown_verifica_raises():
    with pytest.raises(KeyNotFound):
        fattori_resistenza("scivolamento_letto_ancoraggio")

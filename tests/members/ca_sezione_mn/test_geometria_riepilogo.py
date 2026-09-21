"""`geometria_riepilogo.py`: Ac/As/rho geometric summary."""
import pytest

from strutture.members.ca_sezione_mn.geometria_riepilogo import riepilogo_geometrico
from strutture.shared.sezione_ca.modelli import MaterialiSezione, Sezione

pytestmark = pytest.mark.unit


def test_riepilogo_sezione_rettangolare_con_barre(sezione_rettangolare: Sezione) -> None:
    output = riepilogo_geometrico(sezione_rettangolare)
    assert output.ac_mm2 == pytest.approx(300.0 * 500.0)
    assert output.n_barre == 6
    area_barra = 3.141592653589793 * 20.0 ** 2 / 4.0
    assert output.as_mm2 == pytest.approx(6 * area_barra)
    assert output.rho == pytest.approx(output.as_mm2 / output.ac_mm2)


def test_riepilogo_senza_armatura(materiali: MaterialiSezione) -> None:
    sezione = Sezione(contorno=((-150.0, -250.0), (150.0, -250.0), (150.0, 250.0), (-150.0, 250.0)), materiali=materiali)
    output = riepilogo_geometrico(sezione)
    assert output.n_barre == 0
    assert output.as_mm2 == 0.0
    assert output.rho == 0.0

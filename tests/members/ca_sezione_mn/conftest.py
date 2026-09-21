"""Shared fixtures for `ca_sezione_mn` tests: a materials set and a small rectangular section with
a symmetric 3+3 bar layout, reused across the step-module tests."""
import pytest

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.sezione_ca import forme
from strutture.shared.sezione_ca.modelli import Barra, MaterialiSezione, Sezione

B_MM, H_MM = 300.0, 500.0
COPRIFERRO_MM, DIAMETRO_MM = 30.0, 20.0


@pytest.fixture
def materiali() -> MaterialiSezione:
    return MaterialiSezione(calcestruzzo=concrete_properties("C25/30"), acciaio=rebar_properties("B450C"))


@pytest.fixture
def sezione_rettangolare(materiali: MaterialiSezione) -> Sezione:
    contorno = forme.rettangolo(B_MM, H_MM)
    barre = (
        *forme.fila_superiore(B_MM, H_MM, COPRIFERRO_MM, 3, DIAMETRO_MM),
        *forme.fila_inferiore(B_MM, H_MM, COPRIFERRO_MM, 3, DIAMETRO_MM),
    )
    return Sezione(contorno=contorno, barre=barre, materiali=materiali)


@pytest.fixture
def barra() -> Barra:
    return Barra(x_mm=0.0, y_mm=0.0, diametro_mm=16.0)

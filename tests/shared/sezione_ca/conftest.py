"""Shared fixtures for the RC section engine tests."""
import pytest

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.sezione_ca.modelli import MaterialiSezione


@pytest.fixture
def materiali_c25_b450c() -> MaterialiSezione:
    return MaterialiSezione(calcestruzzo=concrete_properties("C25/30"), acciaio=rebar_properties("B450C"))


@pytest.fixture
def materiali_c25_b450c_bilineare() -> MaterialiSezione:
    return MaterialiSezione(
        calcestruzzo=concrete_properties("C25/30"),
        acciaio=rebar_properties("B450C"),
        legge_calcestruzzo="bilineare",
    )

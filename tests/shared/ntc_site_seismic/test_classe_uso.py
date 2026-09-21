"""Unit tests for coefficiente_uso (NTC 2018 §2.4.2 Tab. 2.4.II)."""
import pytest

from strutture.shared.ntc_site_seismic.classe_uso import coefficiente_uso
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("classe", "cu"),
    [("I", 0.7), ("II", 1.0), ("III", 1.5), ("IV", 2.0)],
)
def test_coefficiente_uso_per_classe(classe, cu):
    assert coefficiente_uso(classe) == pytest.approx(cu)


def test_coefficiente_uso_case_insensitive():
    assert coefficiente_uso("ii") == pytest.approx(1.0)


def test_coefficiente_uso_unknown_classe_raises():
    with pytest.raises(KeyNotFound):
        coefficiente_uso("V")

import pytest

from strutture.geotechnics.cedimenti_elastico.boundary import to_kpa, to_m


@pytest.mark.unit
def test_si_is_identity():
    assert to_m(3.5, "SI") == 3.5
    assert to_kpa(90.0, "SI") == 90.0


@pytest.mark.unit
def test_tecnico_converts_cm_and_kgcm2():
    assert to_m(350.0, "tecnico") == pytest.approx(3.5, rel=1e-9)
    assert to_kpa(0.5, "tecnico") == pytest.approx(49.03325, rel=1e-9)

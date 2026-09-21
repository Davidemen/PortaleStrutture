"""Unit tests for `converti_in_si` (docs/architecture-batch2.md §9-D1: boundary unit conversion)."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.ingresso import converti_in_si
from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput

_STRATO = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}


@pytest.mark.unit
def test_si_is_identity() -> None:
    inputs = EdometricoInput(sistema_unita="SI", b=3.5, l=5.0, d=0.2, gamma=18.0, q=50.0, strati=[_STRATO])
    si = converti_in_si(inputs)
    assert si.b_m == pytest.approx(3.5)
    assert si.l_m == pytest.approx(5.0)
    assert si.d_m == pytest.approx(0.2)
    assert si.gamma_kN_m3 == pytest.approx(18.0)
    assert si.q_kPa == pytest.approx(50.0)
    assert si.dz_m == pytest.approx(0.1)
    assert si.z_max_m == pytest.approx(50.0)


@pytest.mark.unit
def test_tecnico_converts_length_gamma_and_pressure() -> None:
    inputs = EdometricoInput(sistema_unita="tecnico", b=350, l=500, gamma=1800, q=0.5, strati=[_STRATO], dz=10, z_max=5000)
    si = converti_in_si(inputs)
    assert si.b_m == pytest.approx(3.5)
    assert si.l_m == pytest.approx(5.0)
    assert si.gamma_kN_m3 == pytest.approx(17.65197, rel=1e-6)
    assert si.q_kPa == pytest.approx(49.03325, rel=1e-6)
    assert si.dz_m == pytest.approx(0.1)
    assert si.z_max_m == pytest.approx(50.0)


@pytest.mark.unit
def test_d_is_never_converted_even_in_tecnico() -> None:
    """`d` (embedment) is metres in the sheet itself, both systems — see `models.py`/`ingresso.py`."""
    inputs = EdometricoInput(sistema_unita="tecnico", b=350, l=500, d=1.2, gamma=1800, q=0.5, strati=[_STRATO])
    si = converti_in_si(inputs)
    assert si.d_m == pytest.approx(1.2)


@pytest.mark.unit
def test_z_crit_input_converted_like_a_length() -> None:
    inputs = EdometricoInput(sistema_unita="tecnico", b=350, l=500, gamma=1800, q=0.5, strati=[_STRATO], z_crit_input=770)
    si = converti_in_si(inputs)
    assert si.z_crit_input_m == pytest.approx(7.7)


@pytest.mark.unit
def test_z_crit_input_none_stays_none() -> None:
    inputs = EdometricoInput(sistema_unita="SI", b=3.5, l=5.0, gamma=18.0, q=50.0, strati=[_STRATO])
    assert converti_in_si(inputs).z_crit_input_m is None


@pytest.mark.unit
def test_falda_none_stays_none() -> None:
    inputs = EdometricoInput(sistema_unita="tecnico", b=350, l=500, gamma=1800, q=0.5, strati=[_STRATO])
    assert converti_in_si(inputs).falda_m is None


@pytest.mark.unit
def test_falda_converted_like_a_length_in_tecnico() -> None:
    inputs = EdometricoInput(sistema_unita="tecnico", b=350, l=500, gamma=1800, q=0.5, strati=[_STRATO], falda=250)
    assert converti_in_si(inputs).falda_m == pytest.approx(2.5)


@pytest.mark.unit
def test_falda_is_identity_in_si() -> None:
    inputs = EdometricoInput(sistema_unita="SI", b=3.5, l=5.0, gamma=18.0, q=50.0, strati=[_STRATO], falda=2.5)
    assert converti_in_si(inputs).falda_m == pytest.approx(2.5)

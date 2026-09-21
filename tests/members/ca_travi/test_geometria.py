import pytest

from strutture.members.ca_travi.geometria import altezza_utile_mm, braccio_leva_mm
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_altezza_utile_subtracts_cover():
    assert altezza_utile_mm(400, 70) == pytest.approx(330)


@pytest.mark.unit
def test_altezza_utile_rejects_non_positive_result():
    with pytest.raises(CalcError):
        altezza_utile_mm(400, 400)
    with pytest.raises(CalcError):
        altezza_utile_mm(400, 450)


@pytest.mark.unit
def test_braccio_leva_is_0_9_d():
    assert braccio_leva_mm(330) == pytest.approx(297)

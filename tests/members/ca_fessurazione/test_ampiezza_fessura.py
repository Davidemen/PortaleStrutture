import pytest

from strutture.members.ca_fessurazione.ampiezza_fessura import apertura_fessure_wk_mm, utilizzo_apertura_fessure

pytestmark = pytest.mark.unit


def test_apertura_fessure_wk_mm():
    assert apertura_fessure_wk_mm(1.7, 0.001, 130.62) == pytest.approx(1.7 * 0.001 * 130.62, rel=1e-9)


def test_utilizzo_apertura_fessure_rounds_up_to_2_decimals():
    # 0.221... -> ceil(22.1)/100 = 23/100 = 0.23
    assert utilizzo_apertura_fessure(wk_mm=0.221, wlim_mm=1.0) == pytest.approx(0.23, rel=1e-9)


def test_utilizzo_apertura_fessure_rejects_non_positive_wlim():
    with pytest.raises(ValueError, match="wlim_mm"):
        utilizzo_apertura_fessure(wk_mm=0.2, wlim_mm=0)

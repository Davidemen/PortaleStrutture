import pytest

from strutture.members.ca_fessurazione.geometria_fessurazione import (
    altezza_efficace_mm,
    altezza_utile_mm,
    area_efficace_mm2,
    diametro_equivalente_mm,
    rapporto_armatura_efficace,
)

pytestmark = pytest.mark.unit


def test_altezza_utile():
    assert altezza_utile_mm(h_mm=250, phi1_mm=20, copriferro_mm=35) == pytest.approx(205, rel=1e-9)


def test_altezza_efficace_picks_the_minimum_branch():
    # 2.5*(h-d)=2.5*45=112.5, (h-x)/3=58.0533, h/2=125 -> min is (h-x)/3
    assert altezza_efficace_mm(h_mm=250, d_mm=205, x_mm=75.84) == pytest.approx(58.0533333, rel=1e-6)


def test_altezza_efficace_can_pick_each_branch():
    assert altezza_efficace_mm(h_mm=100, d_mm=99, x_mm=10) == pytest.approx(2.5, rel=1e-9)  # 2.5*(h-d)
    assert altezza_efficace_mm(h_mm=100, d_mm=10, x_mm=97) == pytest.approx(1.0, rel=1e-9)  # (h-x)/3
    assert altezza_efficace_mm(h_mm=500, d_mm=0, x_mm=-300) == pytest.approx(250.0, rel=1e-9)  # h/2


def test_area_efficace():
    assert area_efficace_mm2(hc_eff_mm=58.0533333, b_mm=1000) == pytest.approx(58053.3333, rel=1e-6)


def test_diametro_equivalente_single_group():
    assert diametro_equivalente_mm(n1=5, phi1_mm=20, n2=0, phi2_mm=0) == pytest.approx(20, rel=1e-9)


def test_diametro_equivalente_two_groups():
    result = diametro_equivalente_mm(n1=3, phi1_mm=16, n2=2, phi2_mm=12)
    assert result == pytest.approx((3 * 16**2 + 2 * 12**2) / (3 * 16 + 2 * 12), rel=1e-9)


def test_diametro_equivalente_rejects_no_bars():
    with pytest.raises(ValueError, match="ø>0"):
        diametro_equivalente_mm(n1=0, phi1_mm=0, n2=0, phi2_mm=0)


def test_rapporto_armatura_efficace():
    assert rapporto_armatura_efficace(as_mm2=1570.8, ac_eff_mm2=58053.3) == pytest.approx(0.0270578, rel=1e-5)


def test_rapporto_armatura_efficace_rejects_non_positive_area():
    with pytest.raises(ValueError, match="positiva"):
        rapporto_armatura_efficace(as_mm2=100, ac_eff_mm2=0)

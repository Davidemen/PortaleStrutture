"""Golden test: spec's §8 cached case, `legacy_compat=True`, end to end through the chain."""
import pytest

from strutture.shared.ntc_site_seismic.amplificazione import amplificazione
from strutture.shared.ntc_site_seismic.classe_uso import coefficiente_uso
from strutture.shared.ntc_site_seismic.periodi_spettro import periodi_spettro
from strutture.shared.ntc_site_seismic.periodo_ritorno import periodi_ritorno
from strutture.shared.ntc_site_seismic.vita_riferimento import vita_riferimento

pytestmark = pytest.mark.golden


def test_golden_case_sisma_brembate():
    cu = coefficiente_uso("II")
    assert cu == pytest.approx(1)

    vr_result = vita_riferimento(50, cu, legacy_compat=True)
    assert vr_result.vr == pytest.approx(50)

    tr = periodi_ritorno(vr_result.vr)
    assert (tr.slo, tr.sld, tr.slv, tr.slc) == pytest.approx((30, 50, 475, 975))

    amp = amplificazione("B", "T1", tc_star_s=0.272, f0=2.436, ag_g=0.098, legacy_compat=True)
    assert amp.cc == pytest.approx(1.42718, rel=1e-6)
    assert amp.ss == pytest.approx(1.2)
    assert amp.st == pytest.approx(1)
    assert amp.s == pytest.approx(1.2)

    periodi = periodi_spettro(amp.cc, tc_star_s=0.272, ag_g=0.098)
    assert periodi.tb == pytest.approx(0.129398, rel=1e-5)
    assert periodi.tc == pytest.approx(0.388193, rel=1e-5)
    assert periodi.td == pytest.approx(1.992, rel=1e-6)

"""Unit tests for amplificazione() composing Ss/Cc/ST/S (NTC 2018 §3.2.2/§3.2.3.2.1)."""
import pytest

from strutture.shared.ntc_site_seismic.amplificazione import amplificazione

pytestmark = pytest.mark.unit


def test_amplificazione_s_equals_st_times_ss():
    result = amplificazione("B", "T2", tc_star_s=0.272, f0=2.436, ag_g=0.098)
    assert result.ss == pytest.approx(1.2)
    assert result.st == pytest.approx(1.2)
    assert result.s == pytest.approx(1.44)


def test_amplificazione_legacy_compat_propagates_to_ss():
    fixed = amplificazione("B", "T1", tc_star_s=0.272, f0=2.5, ag_g=1.1, legacy_compat=False)
    legacy = amplificazione("B", "T1", tc_star_s=0.272, f0=2.5, ag_g=1.1, legacy_compat=True)
    assert fixed.ss == pytest.approx(1.00)
    assert legacy.ss == pytest.approx(0.40)
    assert fixed.cc == pytest.approx(legacy.cc)  # Cc is unaffected by legacy_compat

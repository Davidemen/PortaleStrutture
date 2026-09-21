"""Fixed-behaviour tests for vita_riferimento (NTC 2018 §2.4.3 eq. 3.2.0) — the 35-year floor divergence."""
import pytest

from strutture.shared.ntc_site_seismic.vita_riferimento import vita_riferimento

pytestmark = pytest.mark.unit


def test_vita_riferimento_above_floor_unaffected():
    result = vita_riferimento(50, 1.0)
    assert result.cu == pytest.approx(1.0)
    assert result.vr == pytest.approx(50.0)


def test_vita_riferimento_legacy_compat_omits_floor():
    # VN=10, Cu=0.7 -> VR=7 anni; the sheet does not enforce the 35-year minimum.
    result = vita_riferimento(10, 0.7, legacy_compat=True)
    assert result.vr == pytest.approx(7.0)


def test_vita_riferimento_fixed_behaviour_applies_35_year_floor():
    # Same case with legacy_compat=False (default): VR is floored to 35 anni per NTC2018 §2.4.3.
    result = vita_riferimento(10, 0.7, legacy_compat=False)
    assert result.vr == pytest.approx(35.0)


def test_vita_riferimento_floor_boundary_exact():
    # VN*Cu == 35 exactly: no clamp needed either way.
    result = vita_riferimento(50, 0.7)
    assert result.vr == pytest.approx(35.0)

"""Unit tests for `parametri_sismici` — S = Ss·ST always computed live from the category inputs
(muro rows 17-20; see docs/specs/muro-sostegno.md "Tratto A vs B" and docs/divergences/muro-sostegno.md)."""
import pytest

from strutture.members.muro.parametri_sismici import parametri_sismici

pytestmark = pytest.mark.unit


def test_parametri_sismici_tratto_a_category_c():
    result = parametri_sismici("C", "T1", f0=2.419, ag_g=0.136)
    assert result.ss == pytest.approx(1.5, rel=1e-3)
    assert result.st == pytest.approx(1.0)
    assert result.s == pytest.approx(1.5, rel=1e-3)


def test_parametri_sismici_is_live_not_frozen():
    """Unlike Tratto A's hardcoded I18, changing the category/ag/F0 changes Ss (no stale value)."""
    low = parametri_sismici("C", "T1", f0=1.5, ag_g=0.3)
    high = parametri_sismici("C", "T1", f0=2.419, ag_g=0.136)
    assert low.ss != pytest.approx(high.ss)


def test_parametri_sismici_topografia_scales_s():
    flat = parametri_sismici("C", "T1", f0=2.419, ag_g=0.136)
    ridge = parametri_sismici("C", "T4", f0=2.419, ag_g=0.136)
    assert ridge.st == pytest.approx(1.4)
    assert ridge.s == pytest.approx(flat.ss * 1.4, rel=1e-3)

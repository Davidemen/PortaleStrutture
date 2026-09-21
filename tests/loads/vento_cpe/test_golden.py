import pytest

from strutture.loads.vento_cpe.models import VentoCpeInput
from strutture.loads.vento_cpe.tool import run


@pytest.mark.golden
def test_golden_case():
    """Spec §8: b=15, d=12, h=9 (sheet Foglio1)."""
    report = run(VentoCpeInput(b=15, d=12, h=9, legacy_compat=True))
    assert report.ok
    data = report.data

    assert data.classification == "EDIFICIO TOZZO"  # legacy_compat=True: stringa esatta del foglio

    assert data.dir1.h_d == pytest.approx(0.75, rel=1e-6)
    assert data.dir1.cpe_windward == pytest.approx(0.775, rel=1e-6)
    assert data.dir1.cpe_side == pytest.approx(-0.9, rel=1e-6)
    assert data.dir1.cpe_leeward == pytest.approx(-0.45, rel=1e-6)

    assert data.dir2.h_d == pytest.approx(0.6, rel=1e-6)
    assert data.dir2.cpe_windward == pytest.approx(0.76, rel=1e-6)
    assert data.dir2.cpe_side == pytest.approx(-0.9, rel=1e-6)
    assert data.dir2.cpe_leeward == pytest.approx(-0.42, rel=1e-6)

import pytest

from strutture.loads.vento.models import VentoPressioneInput
from strutture.loads.vento.tool import run


@pytest.mark.golden
def test_golden_case():
    """Spec §8 (sheet Vento): comune=Milano, as=120, TR=50, categoria=II, ct=1, H=60."""
    inputs = VentoPressioneInput(
        comune="Milano",
        altitudine_m=120,
        periodo_ritorno_anni=50,
        categoria_esposizione="II",
        ct=1,
        altezza_edificio_m=60,
        n_sezioni=1000,
        legacy_compat=True,
    )
    report = run(inputs)
    assert report.ok
    data = report.data

    assert data.provincia == "Milano"
    assert data.regione == "Lombardia"
    assert data.zona == 1
    assert data.vb0 == pytest.approx(25, rel=1e-6)
    assert data.a0 == pytest.approx(1000, rel=1e-6)
    assert data.ka == pytest.approx(0.01, rel=1e-6)
    assert data.ks == pytest.approx(0.40, rel=1e-6)
    assert data.ca == pytest.approx(1.0, rel=1e-6)
    assert data.vref == pytest.approx(25, rel=1e-6)
    assert data.a_r == pytest.approx(1.00073, rel=1e-5)
    assert data.vr == pytest.approx(25, rel=1e-6)
    assert data.kr == pytest.approx(0.19, rel=1e-6)
    assert data.z0 == pytest.approx(0.05, rel=1e-6)
    assert data.zmin == pytest.approx(4, rel=1e-6)
    assert data.qb == pytest.approx(0.390625, rel=1e-6)
    assert data.ce_h == pytest.approx(3.60638, rel=1e-5)
    assert data.p_h_kNm2 == pytest.approx(1.409, abs=1e-3)

    # Tabelle profile cross-checks (spec §8): constant below zmin, top row == scalar H37/H45.
    assert data.profilo[0].p_kNm2 == pytest.approx(0.703, abs=1e-3)
    assert data.profilo[-1].z_m == pytest.approx(60, rel=1e-6)
    assert data.profilo[-1].ce == pytest.approx(data.ce_h, rel=1e-9)
    assert data.profilo[-1].p_kNm2 == pytest.approx(1.40874, rel=1e-4)

import pytest

from strutture.loads.neve.models import AccumuloInput, CaricoFaldaInput
from strutture.loads.neve.tool import run_accumulo, run_carico_falda


@pytest.mark.golden
def test_golden_carico_falda_una_falda():
    """Spec §8: Mapello, as=250, Normale, Ct=1, una falda, a=0, parapetto=NO."""
    inputs = CaricoFaldaInput(
        comune="Mapello",
        as_m=250,
        topografia="Normale",
        ct=1,
        tipo_copertura="Copertura ad una falda",
        a=0,
        parapetto="NO",
        a1=35,
        parapetto1="NO",
        a2=50,
        parapetto2="NO",
        legacy_compat=True,
    )
    report = run_carico_falda(inputs)
    assert report.ok
    data = report.data

    assert data.provincia == "Bergamo"
    assert data.regione == "Lombardia"
    assert data.zona == "I (alpina)"
    assert data.qsk == pytest.approx(1.55392, rel=1e-6)
    assert data.ce == pytest.approx(1, rel=1e-6)
    assert data.mu == pytest.approx(0.8, rel=1e-6)
    # spec's cached qs is rounded to 5 decimals; compare at the precision it was given
    assert data.qs == pytest.approx(1.24314, rel=1e-5)


@pytest.mark.golden
def test_golden_carico_falda_due_falde():
    """Spec §8: same H5/H9/H13/H26, a1=35/NO, a2=50/NO."""
    inputs = CaricoFaldaInput(
        comune="Mapello",
        as_m=250,
        topografia="Normale",
        ct=1,
        tipo_copertura="Copertura a due falde",
        a=0,
        parapetto="NO",
        a1=35,
        parapetto1="NO",
        a2=50,
        parapetto2="NO",
        legacy_compat=True,
    )
    report = run_carico_falda(inputs)
    assert report.ok
    data = report.data

    assert data.mu1 == pytest.approx(0.666667, rel=1e-5)
    assert data.qs1 == pytest.approx(1.03595, rel=1e-5)
    assert data.mu2 == pytest.approx(0.266667, rel=1e-5)
    assert data.qs2 == pytest.approx(0.414379, rel=1e-5)


@pytest.mark.golden
def test_golden_accumulo():
    """Spec §8: Bergamo, as=249, Normale, Ct=1, b1=43.15, b2=36.2, h=10, gamma=2, a=0, m1=0.8, msup=0.45."""
    inputs = AccumuloInput(
        comune="Bergamo",
        as_m=249,
        topografia="Normale",
        ct=1,
        b1=43.15,
        b2=36.2,
        h=10,
        gamma=2,
        a=0,
        m1_input=0.8,
        msup=0.45,
        legacy_compat=True,
    )
    report = run_accumulo(inputs)
    assert report.ok
    data = report.data

    assert data.zona == "I (alpina)"
    assert data.qsk == pytest.approx(1.5, rel=1e-6)
    assert data.ce == pytest.approx(1, rel=1e-6)
    assert data.ls == pytest.approx(15, rel=1e-6)
    assert data.mw == pytest.approx(3.9675, rel=1e-6)
    assert data.ms == pytest.approx(0, abs=1e-9)
    assert data.m2 == pytest.approx(3.9675, rel=1e-6)
    assert data.m1_final == pytest.approx(0.8, rel=1e-6)
    assert data.m2_final == pytest.approx(3.9675, rel=1e-6)
    assert data.ls_final == pytest.approx(15, rel=1e-6)

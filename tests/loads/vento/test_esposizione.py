import pytest

from strutture.loads.vento.esposizione import coefficiente_esposizione


@pytest.mark.unit
def test_ce_al_di_sopra_di_zmin_matches_golden():
    """Vento!H37, spec §8: categoria II (kr=0.19, z0=0.05, zmin=4), H=60, ct=1."""
    ce = coefficiente_esposizione(z_m=60, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert ce == pytest.approx(3.60638, rel=1e-4)


@pytest.mark.unit
def test_ce_sotto_zmin_e_costante_e_pari_a_ce_di_zmin():
    ce_zero = coefficiente_esposizione(z_m=0, kr=0.19, z0=0.05, zmin=4, ct=1)
    ce_a_meta_zmin = coefficiente_esposizione(z_m=2, kr=0.19, z0=0.05, zmin=4, ct=1)
    ce_a_zmin = coefficiente_esposizione(z_m=4, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert ce_zero == pytest.approx(ce_a_meta_zmin, rel=1e-9)
    assert ce_zero == pytest.approx(ce_a_zmin, rel=1e-9)


@pytest.mark.unit
def test_ce_cresce_con_la_quota_sopra_zmin():
    ce_basso = coefficiente_esposizione(z_m=10, kr=0.19, z0=0.05, zmin=4, ct=1)
    ce_alto = coefficiente_esposizione(z_m=60, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert ce_alto > ce_basso

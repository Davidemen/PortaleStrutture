import pytest

from strutture.loads.vento.profilo import profilo_pressione


@pytest.mark.unit
def test_profilo_ha_n_sezioni_piu_uno_righe_da_0_a_h():
    righe = profilo_pressione(altezza_edificio_m=60, n_sezioni=10, qb=0.390625, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert len(righe) == 11
    assert righe[0].z_m == pytest.approx(0.0)
    assert righe[-1].z_m == pytest.approx(60.0)


@pytest.mark.unit
def test_profilo_e_parametrico_non_limitato_a_1000_sezioni():
    """Spec's PARAMETRIC requirement: any n_sezioni works, not just the sheet's fixed 1000-row table."""
    righe = profilo_pressione(altezza_edificio_m=9, n_sezioni=3, qb=1.0, kr=0.2, z0=0.1, zmin=5, ct=1)
    assert len(righe) == 4
    assert [r.z_m for r in righe] == pytest.approx([0.0, 3.0, 6.0, 9.0])


@pytest.mark.unit
def test_profilo_p_e_qb_volte_ce_riga_per_riga():
    righe = profilo_pressione(altezza_edificio_m=60, n_sezioni=5, qb=0.390625, kr=0.19, z0=0.05, zmin=4, ct=1)
    for riga in righe:
        assert riga.p_kNm2 == pytest.approx(0.390625 * riga.ce, rel=1e-9)


@pytest.mark.unit
def test_ultima_riga_coincide_con_ce_e_qz_in_sommita():
    """The top row (n=n_sezioni, z=H) must reproduce the scalar ce(H)/qb*ce(H) values exactly."""
    righe = profilo_pressione(altezza_edificio_m=60, n_sezioni=1000, qb=0.390625, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert righe[-1].ce == pytest.approx(3.60638, rel=1e-4)
    assert righe[-1].p_kNm2 == pytest.approx(1.409, abs=1e-3)


@pytest.mark.unit
def test_prima_riga_sotto_zmin_matches_golden_costante():
    """Spec §8 / G40 label: pressure is constant = 0.703 kN/m2 up to zmin (row 0 has z=0<zmin)."""
    righe = profilo_pressione(altezza_edificio_m=60, n_sezioni=1000, qb=0.390625, kr=0.19, z0=0.05, zmin=4, ct=1)
    assert righe[0].p_kNm2 == pytest.approx(0.703, abs=1e-3)

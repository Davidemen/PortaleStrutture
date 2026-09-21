import pytest

from strutture.foundations.plinti_pali.pesi_propri import peso_proprio_kN


@pytest.mark.unit
def test_peso_proprio_golden_case() -> None:
    # docs/specs/fond-plinti-pali.md: AR24 = 4*4*1.2*25*1.3 + 550.7008 = 1174.7008 kN.
    assert peso_proprio_kN(4.0, 4.0, 1.2, 1.3, 550.7008) == pytest.approx(1174.7008, rel=1e-9)


@pytest.mark.unit
def test_peso_proprio_senza_carico_aggiuntivo() -> None:
    assert peso_proprio_kN(2.0, 2.0, 0.5, 1.3, 0.0) == pytest.approx(2.0 * 2.0 * 0.5 * 25.0 * 1.3, rel=1e-9)


@pytest.mark.unit
def test_peso_proprio_rifiuta_geometria_non_positiva() -> None:
    with pytest.raises(ValueError, match="ax_m, by_m, h_plinto_m"):
        peso_proprio_kN(0.0, 4.0, 1.2, 1.3, 0.0)


@pytest.mark.unit
def test_peso_proprio_rifiuta_gamma_g1_non_positivo() -> None:
    with pytest.raises(ValueError, match="gamma_g1"):
        peso_proprio_kN(4.0, 4.0, 1.2, 0.0, 0.0)

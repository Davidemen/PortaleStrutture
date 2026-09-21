import pytest

from strutture.foundations.plinti_isolati.azioni_base import azioni_base
from strutture.foundations.plinti_isolati.pesi_propri import pesi_propri


@pytest.mark.golden
def test_azioni_base_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case, row6 (ULS1)."""
    pesi = pesi_propri(4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 20.0)
    azioni = azioni_base(220.927, 0.131665, 5.37205, -36.4022, 1.31727, pesi, 1.35, 0.8, 0.05, 0.0, 0.0)
    assert azioni.n_kN == pytest.approx(2596.93, rel=1e-5)
    assert azioni.vx_kN == pytest.approx(0.131665, rel=1e-6)
    assert azioni.vy_kN == pytest.approx(5.37205, rel=1e-6)
    assert azioni.myy_kNm == pytest.approx(1.42918, rel=1e-5)
    assert azioni.mxx_kNm == pytest.approx(40.9685, rel=1e-5)


@pytest.mark.unit
def test_azioni_base_eccentricita_utente() -> None:
    """A user eccentricity ex/ey adds N*e to the corresponding base moment."""
    pesi = pesi_propri(4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0)
    senza_ecc = azioni_base(100.0, 0.0, 0.0, 0.0, 0.0, pesi, 1.0, 0.8, 0.0, 0.0, 0.0)
    con_ecc = azioni_base(100.0, 0.0, 0.0, 0.0, 0.0, pesi, 1.0, 0.8, 0.0, 0.1, 0.2)
    assert con_ecc.myy_kNm == pytest.approx(senza_ecc.myy_kNm + con_ecc.n_kN * 0.1)
    assert con_ecc.mxx_kNm == pytest.approx(senza_ecc.mxx_kNm + con_ecc.n_kN * 0.2)


@pytest.mark.unit
def test_azioni_base_carico_non_positivo() -> None:
    pesi = pesi_propri(4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0)
    with pytest.raises(ValueError):
        azioni_base(-1000.0, 0.0, 0.0, 0.0, 0.0, pesi, 1.0, 0.8, 0.0, 0.0, 0.0)

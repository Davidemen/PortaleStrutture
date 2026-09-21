"""`interpolazione.py`: cheap linear read-off of an already-traced M-N domain — the branch split,
the reversal of the negative-N branch, and the "outside the domain" `None`."""
import pytest

from strutture.members.ca_sezione_mn.interpolazione import m_rd_da_dominio
from strutture.shared.sezione_ca.domini import PuntoDominio

pytestmark = pytest.mark.unit


def _dominio_quadrato() -> tuple[PuntoDominio, ...]:
    """A tiny closed domain shaped like `dominio_nm`'s own output: a positive branch with N
    increasing 0 -> 100 -> 200, then a negative branch (N decreasing back 200 -> 100 -> 0) — the
    same "two stitched branches" shape `_rami` expects."""
    return (
        PuntoDominio(n_kN=0.0, m_kNm=0.0),
        PuntoDominio(n_kN=100.0, m_kNm=50.0),
        PuntoDominio(n_kN=200.0, m_kNm=0.0),
        PuntoDominio(n_kN=200.0, m_kNm=0.0),
        PuntoDominio(n_kN=100.0, m_kNm=-40.0),
        PuntoDominio(n_kN=0.0, m_kNm=0.0),
    )


def test_interpolazione_a_meta_ramo() -> None:
    mrd_pos, mrd_neg = m_rd_da_dominio(_dominio_quadrato(), 50.0)
    assert mrd_pos == pytest.approx(25.0)
    assert mrd_neg == pytest.approx(-20.0)


def test_interpolazione_su_un_punto_esistente() -> None:
    mrd_pos, mrd_neg = m_rd_da_dominio(_dominio_quadrato(), 100.0)
    assert mrd_pos == pytest.approx(50.0)
    assert mrd_neg == pytest.approx(-40.0)


def test_n_fuori_dal_dominio_restituisce_none() -> None:
    assert m_rd_da_dominio(_dominio_quadrato(), -10.0) is None
    assert m_rd_da_dominio(_dominio_quadrato(), 300.0) is None


def test_ramo_di_un_solo_punto_usa_il_fallback() -> None:
    """Un ramo degenere di un solo punto non ha coppie da interpolare: `_interpola_ramo` cade sul
    fallback `ramo[-1].m_kNm` invece di lasciare il ciclo a vuoto senza `return`."""
    dominio = (PuntoDominio(n_kN=0.0, m_kNm=0.0), PuntoDominio(n_kN=0.0, m_kNm=0.0))
    mrd_pos, mrd_neg = m_rd_da_dominio(dominio, 0.0)
    assert mrd_pos == pytest.approx(0.0)
    assert mrd_neg == pytest.approx(0.0)


def test_n_agli_estremi_del_dominio() -> None:
    mrd_pos, mrd_neg = m_rd_da_dominio(_dominio_quadrato(), 0.0)
    assert mrd_pos == pytest.approx(0.0)
    assert mrd_neg == pytest.approx(0.0)
    mrd_pos, mrd_neg = m_rd_da_dominio(_dominio_quadrato(), 200.0)
    assert mrd_pos == pytest.approx(0.0)
    assert mrd_neg == pytest.approx(0.0)

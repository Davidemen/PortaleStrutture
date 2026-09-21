"""`rapporto.py`: the utilisation-ratio formulas per `TipoPressoflessione` branch — see the module's
own docstring for the reasoning behind each one (finding CRITICO/ALTO/MEDIO of the engineering
review)."""
import pytest

from strutture.members.ca_sezione_mn.rapporto import esponente_interazione, rapporto, rd_nel_verso
from strutture.members.ca_sezione_mn.rows import AzioneRow

pytestmark = pytest.mark.unit


def _azione(**overrides: object) -> AzioneRow:
    base = {"nome": "C1", "n_ed_kN": 500.0, "m_ed_x_kNm": 0.0, "m_ed_y_kNm": 0.0}
    return AzioneRow.model_validate({**base, **overrides})


def test_rd_nel_verso_sceglie_il_ramo_per_segno() -> None:
    assert rd_nel_verso((100.0, -80.0), 5.0) == pytest.approx(100.0)
    assert rd_nel_verso((100.0, -80.0), -5.0) == pytest.approx(-80.0)
    assert rd_nel_verso((100.0, -80.0), 0.0) == pytest.approx(100.0)


@pytest.mark.parametrize(
    "n_ed_kN,n_rd_kN,atteso",
    [
        (50.0, 1000.0, 1.0),  # N_Ed/N_Rd = 0.05 < 0.1: resta sull'estremo conservativo a=1.0
        (100.0, 1000.0, 1.0),  # esattamente 0.1
        (400.0, 1000.0, 1.25),  # 0.4: interpolato fra (0.1,1.0) e (0.7,1.5)
        (700.0, 1000.0, 1.5),  # esattamente 0.7
        (1000.0, 1000.0, 2.0),  # esattamente 1.0
        (1200.0, 1000.0, 2.0),  # oltre 1.0: resta sull'estremo a=2.0
    ],
)
def test_esponente_interazione_en1992_5_8_9_4(n_ed_kN: float, n_rd_kN: float, atteso: float) -> None:
    assert esponente_interazione(n_ed_kN, n_rd_kN) == pytest.approx(atteso)


def test_esponente_interazione_n_rd_non_positivo_e_conservativo() -> None:
    assert esponente_interazione(500.0, 0.0) == pytest.approx(1.0)


def test_rapporto_uniassiale_x_classico_quando_lintervallo_contiene_zero() -> None:
    azione = _azione(m_ed_x_kNm=50.0)
    assert rapporto("uniassiale x", azione, (100.0, -80.0), (0.0, 0.0), 500.0, 300.0, 1000.0) == pytest.approx(50.0 / 100.0)


def test_rapporto_uniassiale_x_dal_centro_quando_lintervallo_esclude_zero() -> None:
    """[42.5, 56.9] non contiene M=0: centro 49.7, semiampiezza 7.2 — M_Ed=20 è FUORI (> 1)."""
    dentro = rapporto("uniassiale x", _azione(m_ed_x_kNm=53.3), (56.9, 42.5), (0.0, 0.0), 500.0, 300.0, 1000.0)
    fuori = rapporto("uniassiale x", _azione(m_ed_x_kNm=20.0), (56.9, 42.5), (0.0, 0.0), 500.0, 300.0, 1000.0)
    assert dentro == pytest.approx(0.5) and fuori > 1.0


def test_rapporto_uniassiale_x_semiampiezza_nulla_e_m_ed_nullo_da_zero() -> None:
    azione = _azione(m_ed_x_kNm=0.0)
    assert rapporto("uniassiale x", azione, (0.0, 0.0), (0.0, 0.0), 500.0, 300.0, 1000.0) == pytest.approx(0.0)


def test_rapporto_uniassiale_x_semiampiezza_nulla_e_m_ed_non_nullo_da_none() -> None:
    azione = _azione(m_ed_x_kNm=5.0)
    assert rapporto("uniassiale x", azione, (0.0, 0.0), (0.0, 0.0), 500.0, 300.0, 1000.0) is None


def test_rapporto_biassiale_usa_esponente_ec2() -> None:
    azione = _azione(m_ed_x_kNm=50.0, m_ed_y_kNm=30.0)
    r = rapporto("biassiale", azione, (100.0, -80.0), (100.0, -80.0), 500.0, 300.0, 1000.0)
    a = esponente_interazione(500.0, 1000.0)
    assert r == pytest.approx((50.0 / 100.0) ** a + (30.0 / 100.0) ** a)


def test_rapporto_biassiale_con_mrd_nullo_da_none() -> None:
    azione = _azione(m_ed_x_kNm=50.0, m_ed_y_kNm=30.0)
    assert rapporto("biassiale", azione, (0.0, -80.0), (100.0, -80.0), 500.0, 300.0, 1000.0) is None


def test_rapporto_assiale_governa_lasse_con_eccentricita_minima_peggiore() -> None:
    azione = _azione()
    r = rapporto("compressione/trazione semplice", azione, (100.0, -80.0), (100.0, -80.0), 900.0, 1200.0, 1000.0)
    m_min_x, m_min_y = 500.0 * (900.0 / 30.0) / 1000.0, 500.0 * (1200.0 / 30.0) / 1000.0
    rx, ry = m_min_x / 100.0, m_min_y / 100.0
    assert ry > rx  # l'asse y (dimensione maggiore) ha l'eccentricità minima più severa qui
    assert r == pytest.approx(ry)


def test_rapporto_assiale_con_n_ed_nullo_e_zero() -> None:
    azione = _azione(n_ed_kN=0.0)
    r = rapporto("compressione/trazione semplice", azione, (0.0, 0.0), (0.0, 0.0), 500.0, 300.0, 1000.0)
    assert r == pytest.approx(0.0)

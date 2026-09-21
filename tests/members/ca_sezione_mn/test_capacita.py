"""`capacita.py`: per-row pressoflessione check — uniaxial containment-based ratio, biaxial EC2
§5.8.9(4) interaction, minimum-eccentricity axial check, and the "outside the domain" row
(`rapporto=None`, `dentro=False`, never a crash). See `rapporto.py`'s docstring for the formulas."""
import pytest

from strutture.members.ca_sezione_mn.capacita import riga_azione
from strutture.members.ca_sezione_mn.rows import AzioneRow
from strutture.shared.sezione_ca.domini import PuntoDominio

pytestmark = pytest.mark.unit

H_X_MM, H_Y_MM, N_RD_KN = 500.0, 300.0, 1000.0


def _dominio() -> tuple[PuntoDominio, ...]:
    return (
        PuntoDominio(n_kN=0.0, m_kNm=0.0),
        PuntoDominio(n_kN=500.0, m_kNm=100.0),
        PuntoDominio(n_kN=1000.0, m_kNm=0.0),
        PuntoDominio(n_kN=1000.0, m_kNm=0.0),
        PuntoDominio(n_kN=500.0, m_kNm=-80.0),
        PuntoDominio(n_kN=0.0, m_kNm=0.0),
    )


def _azione(**overrides: object) -> AzioneRow:
    base = {"nome": "C1", "n_ed_kN": 500.0, "m_ed_x_kNm": 0.0, "m_ed_y_kNm": 0.0}
    return AzioneRow.model_validate({**base, **overrides})


def _riga(azione: AzioneRow, h_x_mm: float = H_X_MM, h_y_mm: float = H_Y_MM, n_rd_kN: float = N_RD_KN):
    return riga_azione(azione, _dominio(), _dominio(), h_x_mm, h_y_mm, n_rd_kN)


def test_uniassiale_x_positivo() -> None:
    """A N=500 il ramo positivo dà M_Rd+=100, il negativo M_Rd-=-80: l'intervallo contiene M=0,
    quindi il rapporto è quello classico M_Ed/M_Rd nel verso di M_Ed (50/100), il numero che il
    progettista si aspetta — la regola vive nel motore (`sezione_ca.verifica.rapporto_uniassiale`)."""
    riga = _riga(_azione(m_ed_x_kNm=50.0))
    assert riga.tipo == "uniassiale x"
    assert riga.mx_rd_kNm == pytest.approx(100.0)
    assert riga.rapporto == pytest.approx(50.0 / 100.0)
    assert riga.dentro is True


def test_uniassiale_x_negativo_sceglie_il_ramo_negativo_per_mx_rd() -> None:
    riga = _riga(_azione(m_ed_x_kNm=-40.0))
    assert riga.mx_rd_kNm == pytest.approx(-80.0)
    assert riga.rapporto == pytest.approx(40.0 / 80.0)


def test_uniassiale_y() -> None:
    riga = _riga(_azione(m_ed_y_kNm=60.0))
    assert riga.tipo == "uniassiale y"
    assert riga.my_rd_kNm == pytest.approx(100.0)
    assert riga.rapporto == pytest.approx(60.0 / 100.0)


def test_dentro_segue_esattamente_lintervallo_mrd_meno_mrd_piu() -> None:
    """Finding CRITICO (capacita._rd_nel_verso/_rapporto_componente): `dentro` deve seguire
    esattamente `M_Rd- <= M_Ed <= M_Rd+` (qui `[-80, 100]`), non "stesso segno di M_Ed E rapporto
    con quel solo ramo < 1" — un punto appena oltre il bordo va marcato fuori."""
    assert _riga(_azione(m_ed_x_kNm=-80.0)).dentro is True  # esattamente sul bordo
    assert _riga(_azione(m_ed_x_kNm=-80.001)).dentro is False  # appena oltre


def test_biassiale_usa_lesponente_ec2_5_8_9_4() -> None:
    """N_Ed/N_Rd = 500/1000 = 0.5 -> esponente a interpolato fra (0.1, 1.0) e (0.7, 1.5):
    a = 1.0 + (0.5-0.1)/(0.7-0.1)*(1.5-1.0) = 4/3. M_Rd nel verso di M_Ed è 100 su entrambi gli
    assi (stesso dominio sintetico): rapporto = (50/100)^a + (30/100)^a."""
    riga = _riga(_azione(m_ed_x_kNm=50.0, m_ed_y_kNm=30.0))
    assert riga.tipo == "biassiale"
    a = 1.0 + (0.5 - 0.1) / (0.7 - 0.1) * (1.5 - 1.0)
    assert riga.rapporto == pytest.approx((50.0 / 100.0) ** a + (30.0 / 100.0) ** a)


def test_compressione_semplice_usa_leccentricita_minima_en1992_6_1_4() -> None:
    """M_Ed,x = M_Ed,y = 0: il rapporto non è 0 a prescindere, ma quello del momento da
    eccentricità minima e0 = max(h/30, 20 mm) su ciascun asse, governa l'asse peggiore."""
    riga = _riga(_azione(), h_x_mm=900.0, h_y_mm=1200.0)
    assert riga.tipo == "compressione/trazione semplice"
    m_min_x, m_min_y = 500.0 * (900.0 / 30.0) / 1000.0, 500.0 * (1200.0 / 30.0) / 1000.0
    rx, ry = m_min_x / 100.0, m_min_y / 100.0  # intervallo [-80, 100] contiene M=0: rapporto classico
    assert riga.rapporto == pytest.approx(max(rx, ry))
    assert riga.dentro is True


def test_riga_fuori_dal_dominio_non_solleva_e_marca_fuori() -> None:
    riga = _riga(_azione(n_ed_kN=5000.0, m_ed_x_kNm=10.0))
    assert riga.mx_rd_kNm is None and riga.my_rd_kNm is None
    assert riga.rapporto is None
    assert riga.dentro is False


def test_momento_diverso_da_zero_con_mrd_zero_da_rapporto_none() -> None:
    """A N=0 (estremo del dominio di prova) M_Rd = 0 su entrambi i rami: una riga con M_Ed,x != 0
    lì non ha una capacità utilizzabile (rapporto indefinito, non una divisione per zero silenziosa)."""
    riga = _riga(_azione(n_ed_kN=0.0, m_ed_x_kNm=10.0))
    assert riga.mx_rd_kNm == pytest.approx(0.0)
    assert riga.rapporto is None
    assert riga.dentro is False


def test_momento_nullo_da_rapporto_zero_anche_se_mrd_e_zero() -> None:
    """A un'estremità del dominio (N=0) M_Rd = 0 e N_Ed = 0: l'eccentricità minima vale anch'essa 0
    lì (M_min = N_Ed * e0 = 0), quindi il rapporto resta 0 (compressione/trazione pura nulla), non
    un `None` per divisione 0/0."""
    riga = _riga(_azione(n_ed_kN=0.0, m_ed_x_kNm=0.0))
    assert riga.tipo == "compressione/trazione semplice"
    assert riga.rapporto == pytest.approx(0.0)
    assert riga.dentro is True

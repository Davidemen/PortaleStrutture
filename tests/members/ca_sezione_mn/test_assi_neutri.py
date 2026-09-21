"""`assi_neutri.py`: the strain plane of the governing row for the sketch's neutral-axis line only —
uniaxial x/y pick the axis angle, biaxial approximates it from `atan2(My_Ed, Mx_Ed)`, and an
out-of-domain `N_Ed` returns `None` (nothing to draw) instead of raising."""
import pytest

from strutture.members.ca_sezione_mn.assi_neutri import asse_neutro
from strutture.members.ca_sezione_mn.models_output import RigaAzione
from strutture.shared.sezione_ca.domini import intervallo_n
from strutture.shared.sezione_ca.modelli import Sezione

pytestmark = pytest.mark.unit


def _riga(tipo: str, n_ed_kN: float, mx: float = 0.0, my: float = 0.0) -> RigaAzione:
    return RigaAzione(
        nome="G", n_ed_kN=n_ed_kN, m_ed_x_kNm=mx, m_ed_y_kNm=my, tipo=tipo,
        mx_rd_kNm=None, my_rd_kNm=None, rapporto=None, dentro=True,
    )


def test_asse_neutro_uniassiale_x(sezione_rettangolare: Sezione) -> None:
    n_min, n_max = intervallo_n(sezione_rettangolare)
    n_ed = (n_min + n_max) / 2.0
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale x", n_ed, mx=50.0))
    assert piano is not None
    _, kx, ky = piano
    assert ky == pytest.approx(0.0, abs=1e-9)
    assert kx != 0.0


def test_asse_neutro_uniassiale_y(sezione_rettangolare: Sezione) -> None:
    n_min, n_max = intervallo_n(sezione_rettangolare)
    n_ed = (n_min + n_max) / 2.0
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale y", n_ed, my=50.0))
    assert piano is not None
    _, kx, ky = piano
    assert kx == pytest.approx(0.0, abs=1e-9)
    assert ky != 0.0


def test_asse_neutro_biassiale(sezione_rettangolare: Sezione) -> None:
    n_min, n_max = intervallo_n(sezione_rettangolare)
    n_ed = (n_min + n_max) / 2.0
    piano = asse_neutro(sezione_rettangolare, _riga("biassiale", n_ed, mx=40.0, my=40.0))
    assert piano is not None
    _, kx, ky = piano
    assert kx != 0.0 and ky != 0.0


def test_asse_neutro_none_fuori_dal_dominio(sezione_rettangolare: Sezione) -> None:
    _, n_max = intervallo_n(sezione_rettangolare)
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale x", n_max * 10.0, mx=50.0))
    assert piano is None


def test_asse_neutro_compressione_pura_ha_curvatura_nulla(sezione_rettangolare: Sezione) -> None:
    """A N_Ed = N_max (compressione pura) lo stato pivot è uniforme: curvatura nulla, non un
    errore — lo schizzo lo gestisce con una nota dedicata (vedi test_schizzo.py)."""
    _, n_max = intervallo_n(sezione_rettangolare)
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale x", n_max, mx=0.0))
    assert piano is not None
    _, kx, ky = piano
    assert kx == pytest.approx(0.0, abs=1e-9)
    assert ky == pytest.approx(0.0, abs=1e-9)


def test_asse_neutro_compressione_quasi_pura(sezione_rettangolare: Sezione) -> None:
    """Vicino a N_max il piano di deformazione degenere non deve sollevare (guardia `except
    ValueError` in `asse_neutro` per la bisezione)."""
    _, n_max = intervallo_n(sezione_rettangolare)
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale x", n_max * 0.999, mx=1.0))
    assert piano is None or isinstance(piano, tuple)

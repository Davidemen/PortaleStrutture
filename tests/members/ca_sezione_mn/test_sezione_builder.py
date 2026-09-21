"""`sezione_builder.py`: resolves `SezioneMnInput` into the engine's `Sezione` — one test per forma,
per armatura mode, and the CalcError wrapping for a degenerate/invalid geometry."""
import pytest

from strutture.members.ca_sezione_mn.models_input import SezioneMnInput
from strutture.members.ca_sezione_mn.sezione_builder import (
    costruisci_barre,
    costruisci_contorno,
    costruisci_materiali,
    costruisci_sezione,
)
from strutture.shared.report import CalcError
from strutture.shared.sezione_ca import geometria
from strutture.shared.sezione_ca.domini import m_rd as m_rd_esatto
from strutture.shared.sezione_ca.modelli import Sezione

pytestmark = pytest.mark.unit

BASE_AZIONI = ({"nome": "C1", "n_ed_kN": 500.0, "m_ed_x_kNm": 50.0, "m_ed_y_kNm": 0.0},)


def _input(**overrides: object) -> SezioneMnInput:
    base = {
        "forma": "rettangolare", "b_mm": 300.0, "h_mm": 500.0,
        "armatura_modo": "tabella",
        "barre": ({"x_mm": -100.0, "y_mm": 200.0, "diametro_mm": 20.0}, {"x_mm": 100.0, "y_mm": 200.0, "diametro_mm": 20.0}),
        "classe_calcestruzzo": "C25/30", "grado_acciaio": "B450C",
        "azioni": BASE_AZIONI,
    }
    return SezioneMnInput.model_validate({**base, **overrides})


def test_contorno_rettangolare() -> None:
    poligono = costruisci_contorno(_input())
    assert geometria.area(poligono) == pytest.approx(300.0 * 500.0)


def test_contorno_circolare() -> None:
    inputs = _input(forma="circolare", diametro_mm=400.0, b_mm=None, h_mm=None,
                     barre=({"x_mm": 0.0, "y_mm": 100.0, "diametro_mm": 20.0},))
    poligono = costruisci_contorno(inputs)
    assert geometria.area(poligono) == pytest.approx(3.141592653589793 * 200.0 ** 2, rel=5e-3)


def test_contorno_a_t() -> None:
    inputs = _input(forma="a_t", b_mm=None, h_mm=600.0, bf_mm=400.0, hf_mm=150.0, bw_mm=250.0,
                     barre=({"x_mm": 0.0, "y_mm": 50.0, "diametro_mm": 20.0},))
    poligono = costruisci_contorno(inputs)
    attesa = 400.0 * 150.0 + 250.0 * (600.0 - 150.0)
    assert geometria.area(poligono) == pytest.approx(attesa)


def test_contorno_a_l() -> None:
    inputs = _input(forma="a_l", b_mm=None, h_mm=600.0, bf_mm=400.0, hf_mm=150.0, bw_mm=250.0,
                     barre=({"x_mm": 50.0, "y_mm": 50.0, "diametro_mm": 20.0},))
    poligono = costruisci_contorno(inputs)
    attesa = 400.0 * 150.0 + 250.0 * (600.0 - 150.0)
    assert geometria.area(poligono) == pytest.approx(attesa)


def test_contorno_parete() -> None:
    inputs = _input(forma="parete", b_mm=None, h_mm=None, lw_mm=4000.0, tw_mm=250.0, le_mm=500.0, te_mm=600.0,
                     barre=({"x_mm": 0.0, "y_mm": 0.0, "diametro_mm": 20.0},))
    poligono = costruisci_contorno(inputs)
    attesa = 250.0 * (4000.0 - 2 * 500.0) + 2 * 500.0 * 600.0
    assert geometria.area(poligono) == pytest.approx(attesa)


def test_contorno_poligono_libero() -> None:
    vertici = ({"x_mm": 0.0, "y_mm": 0.0}, {"x_mm": 300.0, "y_mm": 0.0}, {"x_mm": 300.0, "y_mm": 300.0}, {"x_mm": 0.0, "y_mm": 300.0})
    inputs = _input(forma="poligono_libero", b_mm=None, h_mm=None, vertici=vertici,
                     barre=({"x_mm": 0.0, "y_mm": 0.0, "diametro_mm": 20.0},))
    poligono = costruisci_contorno(inputs)
    assert geometria.area(poligono) == pytest.approx(300.0 * 300.0)


def test_barre_da_tabella() -> None:
    barre = costruisci_barre(_input())
    assert [(b.x_mm, b.y_mm, b.diametro_mm) for b in barre] == [(-100.0, 200.0, 20.0), (100.0, 200.0, 20.0)]


@pytest.mark.parametrize("layout_tipo,attese", [("fila_superiore", 4), ("fila_inferiore", 4), ("perimetrale", 4 * 4 - 4)])
def test_barre_da_layout_rettangolare(layout_tipo: str, attese: int) -> None:
    inputs = _input(
        armatura_modo="layout", barre=(), layout_tipo=layout_tipo,
        layout_copriferro_mm=30.0, layout_diametro_mm=16.0,
        layout_n_barre=4 if layout_tipo != "perimetrale" else None,
        layout_n_per_lato=4 if layout_tipo == "perimetrale" else None,
    )
    barre = costruisci_barre(inputs)
    assert len(barre) == attese


def test_barre_da_layout_circolare() -> None:
    inputs = _input(
        forma="circolare", b_mm=None, h_mm=None, diametro_mm=400.0,
        armatura_modo="layout", barre=(), layout_tipo="circolare",
        layout_copriferro_mm=30.0, layout_diametro_mm=16.0, layout_n_barre=8,
    )
    barre = costruisci_barre(inputs)
    assert len(barre) == 8


def test_materiali_seguono_classe_e_grado() -> None:
    materiali = costruisci_materiali(_input(classe_calcestruzzo="C32/40", grado_acciaio="B450A"))
    assert materiali.calcestruzzo.classe == "C32/40"
    assert materiali.acciaio.grado == "B450A"
    assert materiali.legge_calcestruzzo == "parabola-rettangolo"
    assert materiali.legge_acciaio == "elastico-perfettamente-plastico"


def test_costruisci_sezione_completa() -> None:
    sezione = costruisci_sezione(_input())
    assert len(sezione.barre) == 2
    assert sezione.materiali.calcestruzzo.classe == "C25/30"


def test_barra_esterna_al_contorno_solleva_calc_error() -> None:
    inputs = _input(barre=({"x_mm": 0.0, "y_mm": 1000.0, "diametro_mm": 20.0},))
    with pytest.raises(CalcError, match="esterna al contorno"):
        costruisci_sezione(inputs)


def test_costruisci_sezione_ricentra_sul_baricentro_per_sezione_a_t() -> None:
    """`forme.sezione_a_t` ha origine al lembo inferiore dell'anima (NON il baricentro): la
    `Sezione` costruita dal tool deve invece avere origine nel proprio baricentro, qualunque sia
    `forma` (finding CRITICO sezione_builder: senza ricentraggio N_Ed/M_Ed verrebbero ridotti a un
    polo diverso dal baricentro plastico)."""
    inputs = _input(forma="a_t", b_mm=None, h_mm=600.0, bf_mm=400.0, hf_mm=150.0, bw_mm=250.0,
                     barre=({"x_mm": 0.0, "y_mm": 50.0, "diametro_mm": 20.0},))
    sezione = costruisci_sezione(inputs)
    cx, cy = geometria.centroide(sezione.contorno)
    assert (cx, cy) == pytest.approx((0.0, 0.0), abs=1e-6)


def test_costruisci_sezione_ricentra_sul_baricentro_per_sezione_a_l() -> None:
    """`forme.sezione_a_l` ha origine nello spigolo esterno (NON il baricentro): stessa correzione
    di `test_costruisci_sezione_ricentra_sul_baricentro_per_sezione_a_t`."""
    inputs = _input(forma="a_l", b_mm=None, h_mm=600.0, bf_mm=400.0, hf_mm=150.0, bw_mm=250.0,
                     barre=({"x_mm": 50.0, "y_mm": 50.0, "diametro_mm": 20.0},))
    sezione = costruisci_sezione(inputs)
    cx, cy = geometria.centroide(sezione.contorno)
    assert (cx, cy) == pytest.approx((0.0, 0.0), abs=1e-6)


def test_costruisci_sezione_trasla_anche_le_barre_dello_stesso_scarto_del_contorno() -> None:
    inputs = _input(forma="a_t", b_mm=None, h_mm=600.0, bf_mm=400.0, hf_mm=150.0, bw_mm=250.0,
                     barre=({"x_mm": 0.0, "y_mm": 50.0, "diametro_mm": 20.0},))
    _, cy_grezzo = geometria.centroide(costruisci_contorno(inputs))
    sezione = costruisci_sezione(inputs)
    assert sezione.barre[0].y_mm == pytest.approx(50.0 - cy_grezzo)


def test_costruisci_sezione_rettangolare_gia_baricentrica_non_trasla() -> None:
    """Un rettangolo è già centrato sul proprio baricentro (`forme.rettangolo`): il ricentraggio
    non deve introdurre alcuno scarto qui, verifica di non-regressione."""
    inputs = _input()
    sezione = costruisci_sezione(inputs)
    assert sezione.contorno == costruisci_contorno(inputs)
    assert (sezione.barre[0].x_mm, sezione.barre[0].y_mm) == (-100.0, 200.0)


def test_costruisci_sezione_il_polo_sposta_il_momento_resistente_dell_atteso() -> None:
    """Riproduce numericamente il finding CRITICO (T 1000/150/300/600, 3phi20 inferiori + 3phi16
    superiori): il M_Rd calcolato sul contorno grezzo (polo del preset) differisce da quello sul
    contorno ricentrato (polo baricentrico) esattamente di N_Ed * y_baricentro — la differenza che il
    tool eliminava silenziosamente prima della correzione."""
    inputs = _input(
        forma="a_t", b_mm=None, h_mm=600.0, bf_mm=1000.0, hf_mm=150.0, bw_mm=300.0,
        barre=(
            {"x_mm": -100.0, "y_mm": 50.0, "diametro_mm": 20.0},
            {"x_mm": 0.0, "y_mm": 50.0, "diametro_mm": 20.0},
            {"x_mm": 100.0, "y_mm": 50.0, "diametro_mm": 20.0},
            {"x_mm": -100.0, "y_mm": 550.0, "diametro_mm": 16.0},
            {"x_mm": 0.0, "y_mm": 550.0, "diametro_mm": 16.0},
            {"x_mm": 100.0, "y_mm": 550.0, "diametro_mm": 16.0},
        ),
    )
    contorno_grezzo = costruisci_contorno(inputs)
    barre_grezze = costruisci_barre(inputs)
    materiali = costruisci_materiali(inputs)
    _, cy_grezzo = geometria.centroide(contorno_grezzo)
    sezione_grezza = Sezione(contorno=contorno_grezzo, barre=barre_grezze, materiali=materiali)
    sezione_corretta = costruisci_sezione(inputs)

    n_ed_kN = 500.0
    mp_grezzo, _ = m_rd_esatto(sezione_grezza, n_ed_kN, "x")
    mp_corretto, _ = m_rd_esatto(sezione_corretta, n_ed_kN, "x")
    assert (mp_grezzo - mp_corretto) == pytest.approx(n_ed_kN * cy_grezzo / 1000.0, rel=1e-2)

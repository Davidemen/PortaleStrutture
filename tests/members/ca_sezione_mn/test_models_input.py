"""`SezioneMnInput`: conditional geometry/armatura validation and non-positive-dimension bounds
(docs/architecture-phase4.md §B, docs/BUILD_CONTRACT.md "Validation with Italian messages")."""
import pytest
from pydantic import ValidationError

from strutture.members.ca_sezione_mn.models_input import SezioneMnInput

pytestmark = pytest.mark.unit

AZIONI = ({"nome": "C1", "n_ed_kN": 500.0, "m_ed_x_kNm": 50.0, "m_ed_y_kNm": 0.0},)
BARRE = ({"x_mm": 0.0, "y_mm": 200.0, "diametro_mm": 20.0},)


def _input(**overrides: object) -> dict:
    base = {
        "forma": "rettangolare", "b_mm": 300.0, "h_mm": 500.0,
        "armatura_modo": "tabella", "barre": BARRE,
        "classe_calcestruzzo": "C25/30", "grado_acciaio": "B450C",
        "azioni": AZIONI,
    }
    return {**base, **overrides}


def test_esempio_valido_rettangolare() -> None:
    SezioneMnInput.model_validate(_input())


@pytest.mark.parametrize(
    "overrides,messaggio",
    [
        ({"b_mm": None}, "base"),
        ({"h_mm": None}, "base"),
    ],
)
def test_rettangolare_richiede_b_e_h(overrides: dict, messaggio: str) -> None:
    with pytest.raises(ValidationError, match="rettangolare"):
        SezioneMnInput.model_validate(_input(**overrides))


def test_circolare_richiede_diametro() -> None:
    with pytest.raises(ValidationError, match="circolare"):
        SezioneMnInput.model_validate(_input(forma="circolare", b_mm=None, h_mm=None))


@pytest.mark.parametrize("forma", ["a_t", "a_l"])
def test_a_t_a_l_richiedono_bf_hf_bw_h(forma: str) -> None:
    with pytest.raises(ValidationError, match="T/a L"):
        SezioneMnInput.model_validate(_input(forma=forma, b_mm=None))


def test_parete_richiede_lw_tw_le_te() -> None:
    with pytest.raises(ValidationError, match="parete"):
        SezioneMnInput.model_validate(_input(forma="parete", b_mm=None, h_mm=None))


def test_poligono_libero_richiede_almeno_3_vertici() -> None:
    with pytest.raises(ValidationError, match="almeno 3 vertici"):
        SezioneMnInput.model_validate(_input(
            forma="poligono_libero", b_mm=None, h_mm=None,
            vertici=({"x_mm": 0.0, "y_mm": 0.0}, {"x_mm": 100.0, "y_mm": 0.0}),
        ))


def test_poligono_libero_con_3_vertici_valido() -> None:
    SezioneMnInput.model_validate(_input(
        forma="poligono_libero", b_mm=None, h_mm=None,
        vertici=({"x_mm": 0.0, "y_mm": 0.0}, {"x_mm": 300.0, "y_mm": 0.0}, {"x_mm": 150.0, "y_mm": 300.0}),
        barre=({"x_mm": 150.0, "y_mm": 50.0, "diametro_mm": 20.0},),
    ))


def test_armatura_tabella_vuota_solleva_errore() -> None:
    with pytest.raises(ValidationError, match="almeno una barra"):
        SezioneMnInput.model_validate(_input(barre=()))


def test_layout_senza_tipo_solleva_errore() -> None:
    with pytest.raises(ValidationError, match="tipo, copriferro e diametro"):
        SezioneMnInput.model_validate(_input(armatura_modo="layout", barre=()))


@pytest.mark.parametrize("layout_tipo", ["fila_superiore", "fila_inferiore", "circolare"])
def test_layout_con_n_barre_richiede_layout_n_barre(layout_tipo: str) -> None:
    with pytest.raises(ValidationError, match="numero di barre"):
        SezioneMnInput.model_validate(_input(
            armatura_modo="layout", barre=(), layout_tipo=layout_tipo,
            layout_copriferro_mm=30.0, layout_diametro_mm=16.0,
            forma="circolare" if layout_tipo == "circolare" else "rettangolare",
            diametro_mm=400.0 if layout_tipo == "circolare" else None,
            b_mm=None if layout_tipo == "circolare" else 300.0,
            h_mm=None if layout_tipo == "circolare" else 500.0,
        ))


def test_layout_perimetrale_richiede_n_per_lato() -> None:
    with pytest.raises(ValidationError, match="numero di barre per lato"):
        SezioneMnInput.model_validate(_input(
            armatura_modo="layout", barre=(), layout_tipo="perimetrale",
            layout_copriferro_mm=30.0, layout_diametro_mm=16.0,
        ))


@pytest.mark.parametrize("layout_tipo", ["fila_superiore", "fila_inferiore", "perimetrale"])
def test_layout_rettangolare_richiede_forma_rettangolare(layout_tipo: str) -> None:
    with pytest.raises(ValidationError, match="sezione rettangolare"):
        SezioneMnInput.model_validate(_input(
            forma="circolare", b_mm=None, h_mm=None, diametro_mm=400.0,
            armatura_modo="layout", barre=(), layout_tipo=layout_tipo,
            layout_copriferro_mm=30.0, layout_diametro_mm=16.0,
            layout_n_barre=4, layout_n_per_lato=4,
        ))


def test_layout_circolare_richiede_forma_circolare() -> None:
    with pytest.raises(ValidationError, match="sezione circolare"):
        SezioneMnInput.model_validate(_input(
            armatura_modo="layout", barre=(), layout_tipo="circolare",
            layout_copriferro_mm=30.0, layout_diametro_mm=16.0, layout_n_barre=8,
        ))


@pytest.mark.parametrize("campo,valore", [("b_mm", 0.0), ("b_mm", -100.0), ("h_mm", 0.0), ("h_mm", -100.0)])
def test_dimensioni_non_positive_sono_rifiutate(campo: str, valore: float) -> None:
    with pytest.raises(ValidationError):
        SezioneMnInput.model_validate(_input(**{campo: valore}))


def test_diametro_barra_non_positivo_e_rifiutato() -> None:
    with pytest.raises(ValidationError):
        SezioneMnInput.model_validate(_input(barre=({"x_mm": 0.0, "y_mm": 200.0, "diametro_mm": 0.0},)))


def test_tabella_azioni_richiede_almeno_una_riga() -> None:
    with pytest.raises(ValidationError):
        SezioneMnInput.model_validate(_input(azioni=()))


def test_nessun_campo_legacy_compat() -> None:
    assert "legacy_compat" not in SezioneMnInput.model_fields


@pytest.mark.parametrize("layout_tipo", ["fila_superiore", "fila_inferiore"])
def test_layout_copriferro_troppo_grande_per_rettangolare_solleva_errore(layout_tipo: str) -> None:
    """b=300, h=500: semilato minimo = 150 mm; copriferro 150 + phi/2 = 158 mm >= 150 mm, le barre
    del layout finirebbero oltre l'asse di simmetria (finding MEDIO models_input._valida_armatura:
    nessun limite legava il copriferro a b/h)."""
    with pytest.raises(ValidationError, match="copriferro troppo grande"):
        SezioneMnInput.model_validate(_input(
            armatura_modo="layout", barre=(), layout_tipo=layout_tipo,
            layout_copriferro_mm=150.0, layout_diametro_mm=16.0, layout_n_barre=3,
        ))


def test_layout_copriferro_perimetrale_troppo_grande_solleva_errore() -> None:
    with pytest.raises(ValidationError, match="copriferro troppo grande"):
        SezioneMnInput.model_validate(_input(
            armatura_modo="layout", barre=(), layout_tipo="perimetrale",
            layout_copriferro_mm=200.0, layout_diametro_mm=16.0, layout_n_per_lato=4,
        ))


def test_layout_copriferro_circolare_troppo_grande_solleva_errore() -> None:
    with pytest.raises(ValidationError, match="copriferro troppo grande"):
        SezioneMnInput.model_validate(_input(
            forma="circolare", b_mm=None, h_mm=None, diametro_mm=400.0,
            armatura_modo="layout", barre=(), layout_tipo="circolare",
            layout_copriferro_mm=195.0, layout_diametro_mm=16.0, layout_n_barre=8,
        ))


def test_layout_copriferro_entro_i_limiti_e_accettato() -> None:
    SezioneMnInput.model_validate(_input(
        armatura_modo="layout", barre=(), layout_tipo="perimetrale",
        layout_copriferro_mm=30.0, layout_diametro_mm=16.0, layout_n_per_lato=4,
    ))

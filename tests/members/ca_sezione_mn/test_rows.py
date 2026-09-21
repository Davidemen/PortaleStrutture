"""Table row models: `BarraRow`, `VerticeRow`, `AzioneRow` — bounds and max row counts
(`shared.tabular.RowModel`, docs/BUILD_CONTRACT.md "Batch 2")."""
import pytest
from pydantic import ValidationError

from strutture.members.ca_sezione_mn.rows import (
    MAX_AZIONI_ROWS,
    MAX_BARRE_ROWS,
    MAX_VERTICI_ROWS,
    AzioneRow,
    BarraRow,
    VerticeRow,
)

pytestmark = pytest.mark.unit


def test_barra_row_valida() -> None:
    row = BarraRow.model_validate({"x_mm": 10.0, "y_mm": -20.0, "diametro_mm": 16.0})
    assert row.diametro_mm == 16.0


@pytest.mark.parametrize("diametro", [0.0, -5.0, 61.0])
def test_barra_row_diametro_fuori_bounds(diametro: float) -> None:
    with pytest.raises(ValidationError):
        BarraRow.model_validate({"x_mm": 0.0, "y_mm": 0.0, "diametro_mm": diametro})


def test_vertice_row_accetta_coordinate_negative() -> None:
    row = VerticeRow.model_validate({"x_mm": -100.0, "y_mm": -50.0})
    assert (row.x_mm, row.y_mm) == (-100.0, -50.0)


def test_azione_row_default_momenti_nulli() -> None:
    row = AzioneRow.model_validate({"nome": "C1", "n_ed_kN": 500.0})
    assert row.m_ed_x_kNm == 0.0 and row.m_ed_y_kNm == 0.0


def test_azione_row_nome_obbligatorio() -> None:
    with pytest.raises(ValidationError):
        AzioneRow.model_validate({"nome": "", "n_ed_kN": 500.0})


def test_azione_row_n_ed_accetta_trazione_negativa() -> None:
    """N_Ed positivo = compressione (per convenzione dichiarata nella descrizione del campo);
    valori negativi (trazione) sono ammessi, non sono un errore di validazione."""
    row = AzioneRow.model_validate({"nome": "C1", "n_ed_kN": -50.0})
    assert row.n_ed_kN == -50.0


def test_max_rows_costanti() -> None:
    assert (MAX_BARRE_ROWS, MAX_VERTICI_ROWS, MAX_AZIONI_ROWS) == (200, 50, 500)


def test_azione_row_descrizione_dichiara_convenzione_segno() -> None:
    descrizione = AzioneRow.model_fields["n_ed_kN"].description
    assert "compress" in descrizione.lower()


def test_azione_row_descrizioni_momento_dichiarano_la_fibra_tesa() -> None:
    """Finding MEDIO rows.py: la convenzione di segno dei momenti esisteva solo nei docstring del
    motore, non al confine del tool; ora è nelle description dei campi stessi."""
    desc_x = AzioneRow.model_fields["m_ed_x_kNm"].description.lower()
    desc_y = AzioneRow.model_fields["m_ed_y_kNm"].description.lower()
    assert "ordinata minima" in desc_x or "lembo inferiore" in desc_x
    assert "ascissa massima" in desc_y


def test_barra_row_descrizione_dichiara_ricentraggio_sul_baricentro() -> None:
    descrizione = BarraRow.model_fields["x_mm"].description.lower()
    assert "baricentro" in descrizione

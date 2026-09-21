"""`Sezione` validation: simple polygon, ≥ 3 vertices, positive area, CW->CCW reorder, bars inside
the outline."""
import pytest
from pydantic import ValidationError

from strutture.shared.sezione_ca import geometria
from strutture.shared.sezione_ca.modelli import Barra, Sezione


def test_riordina_contorno_orario_in_antiorario(materiali_c25_b450c) -> None:
    orario = ((0.0, 0.0), (0.0, 300.0), (200.0, 300.0), (200.0, 0.0))
    sezione = Sezione(contorno=orario, materiali=materiali_c25_b450c)
    assert geometria.area_con_segno(sezione.contorno) > 0.0
    assert geometria.area(sezione.contorno) == pytest.approx(200.0 * 300.0)


def test_meno_di_tre_vertici_rifiutato(materiali_c25_b450c) -> None:
    with pytest.raises(ValidationError, match="almeno 3 vertici"):
        Sezione(contorno=((0.0, 0.0), (10.0, 0.0)), materiali=materiali_c25_b450c)


def test_area_nulla_rifiutata(materiali_c25_b450c) -> None:
    with pytest.raises(ValidationError, match="area nulla"):
        Sezione(contorno=((0.0, 0.0), (10.0, 0.0), (20.0, 0.0)), materiali=materiali_c25_b450c)


def test_poligono_non_semplice_rifiutato(materiali_c25_b450c) -> None:
    autointersecante = ((0.0, 0.0), (10.0, 0.0), (0.0, 10.0), (6.0, 4.0), (10.0, 10.0))
    with pytest.raises(ValidationError, match="poligono semplice"):
        Sezione(contorno=autointersecante, materiali=materiali_c25_b450c)


def test_barra_interna_accettata(materiali_c25_b450c) -> None:
    contorno = ((-150.0, -250.0), (150.0, -250.0), (150.0, 250.0), (-150.0, 250.0))
    barra = Barra(x_mm=0.0, y_mm=0.0, diametro_mm=16.0)
    sezione = Sezione(contorno=contorno, barre=(barra,), materiali=materiali_c25_b450c)
    assert len(sezione.barre) == 1


def test_barra_esterna_rifiutata(materiali_c25_b450c) -> None:
    contorno = ((-150.0, -250.0), (150.0, -250.0), (150.0, 250.0), (-150.0, 250.0))
    barra = Barra(x_mm=1000.0, y_mm=0.0, diametro_mm=16.0)
    with pytest.raises(ValidationError, match="esterna al contorno"):
        Sezione(contorno=contorno, barre=(barra,), materiali=materiali_c25_b450c)


def test_barra_diametro_non_positivo_rifiutata() -> None:
    with pytest.raises(ValidationError):
        Barra(x_mm=0.0, y_mm=0.0, diametro_mm=0.0)


def test_sezione_e_materiali_sono_frozen(materiali_c25_b450c) -> None:
    contorno = ((-150.0, -250.0), (150.0, -250.0), (150.0, 250.0), (-150.0, 250.0))
    sezione = Sezione(contorno=contorno, materiali=materiali_c25_b450c)
    with pytest.raises(ValidationError):
        sezione.contorno = ()  # type: ignore[misc]

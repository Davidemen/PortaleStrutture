"""Preset outlines and bar layouts — area/shape sanity and bar-count checks."""
import pytest

from strutture.shared.sezione_ca import forme, geometria


def test_sezione_a_t_area() -> None:
    poligono = forme.sezione_a_t(400.0, 150.0, 250.0, 600.0)
    attesa = 400.0 * 150.0 + 250.0 * (600.0 - 150.0)
    assert geometria.area(poligono) == pytest.approx(attesa)
    assert geometria.poligono_semplice(poligono)
    assert geometria.area_con_segno(poligono) > 0.0


def test_sezione_a_l_area() -> None:
    poligono = forme.sezione_a_l(400.0, 150.0, 250.0, 600.0)
    attesa = 400.0 * 150.0 + 250.0 * (600.0 - 150.0)
    assert geometria.area(poligono) == pytest.approx(attesa)
    assert geometria.poligono_semplice(poligono)
    assert geometria.area_con_segno(poligono) > 0.0


def test_parete_con_elementi_estremita_area() -> None:
    poligono = forme.parete_con_elementi_estremita(4000.0, 250.0, 500.0, 600.0)
    attesa = 250.0 * (4000.0 - 2 * 500.0) + 2 * 500.0 * 600.0
    assert geometria.area(poligono) == pytest.approx(attesa)
    assert geometria.poligono_semplice(poligono)
    assert geometria.area_con_segno(poligono) > 0.0


def test_fila_superiore_e_inferiore_conteggio_e_simmetria() -> None:
    sopra = forme.fila_superiore(300.0, 500.0, 30.0, 4, 16.0)
    sotto = forme.fila_inferiore(300.0, 500.0, 30.0, 4, 16.0)
    assert len(sopra) == 4
    assert len(sotto) == 4
    assert sopra[0].y_mm == pytest.approx(-sotto[0].y_mm)
    assert sopra[0].x_mm == pytest.approx(sotto[0].x_mm)


def test_perimetrale_conteggio_spigoli_non_duplicati() -> None:
    barre = forme.perimetrale(300.0, 500.0, 30.0, 3, 16.0)
    assert len(barre) == 4 * (3 - 1)


def test_perimetrale_tutte_le_barre_dentro_il_rettangolo() -> None:
    contorno = forme.rettangolo(300.0, 500.0)
    barre = forme.perimetrale(300.0, 500.0, 30.0, 4, 16.0)
    assert all(geometria.punto_in_poligono((b.x_mm, b.y_mm), contorno, tolleranza_mm=1e-6) for b in barre)


def test_circolare_conteggio_e_raggio() -> None:
    barre = forme.circolare(500.0, 40.0, 8, 20.0)
    assert len(barre) == 8
    raggio_atteso = 500.0 / 2.0 - 40.0 - 20.0 / 2.0
    for barra in barre:
        raggio = (barra.x_mm ** 2 + barra.y_mm ** 2) ** 0.5
        assert raggio == pytest.approx(raggio_atteso)

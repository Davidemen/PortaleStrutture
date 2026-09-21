"""Pure polygon geometry — closed forms and invariants (`docs/architecture-phase4.md` §A)."""
import math

import pytest

from strutture.shared.sezione_ca import forme, geometria


def test_area_rettangolo() -> None:
    poligono = forme.rettangolo(300.0, 500.0)
    assert geometria.area(poligono) == pytest.approx(300.0 * 500.0)


def test_centroide_rettangolo_centrato() -> None:
    poligono = forme.rettangolo(300.0, 500.0)
    cx, cy = geometria.centroide(poligono)
    assert cx == pytest.approx(0.0, abs=1e-9)
    assert cy == pytest.approx(0.0, abs=1e-9)


def test_momenti_centroidali_rettangolo() -> None:
    b, h = 300.0, 500.0
    ixx, iyy, ixy = geometria.momenti_centroidali(forme.rettangolo(b, h))
    assert ixx == pytest.approx(b * h ** 3 / 12.0, rel=1e-9)
    assert iyy == pytest.approx(h * b ** 3 / 12.0, rel=1e-9)
    assert ixy == pytest.approx(0.0, abs=1e-6)


def test_bounding_box_rettangolo() -> None:
    poligono = forme.rettangolo(300.0, 500.0)
    assert geometria.bounding_box(poligono) == pytest.approx((-150.0, -250.0, 150.0, 250.0))


def test_cerchio_48_lati_area_vs_analitica() -> None:
    """48-gon vs analytic circle area: < 0.2 %."""
    d = 400.0
    area_analitica = math.pi * d ** 2 / 4.0
    area_48gon = geometria.area(forme.cerchio(d, n_lati=48))
    assert area_48gon == pytest.approx(area_analitica, rel=2e-3)
    assert area_48gon < area_analitica  # inscribed polygon underestimates the circle


def test_cerchio_48_lati_inerzia_vs_analitica() -> None:
    """48-gon vs analytic circle inertia: < 0.2 %."""
    d = 400.0
    ixx_analitica = math.pi * d ** 4 / 64.0
    ixx, iyy, _ = geometria.momenti_centroidali(forme.cerchio(d, n_lati=48))
    assert ixx == pytest.approx(ixx_analitica, rel=2e-3)
    assert iyy == pytest.approx(ixx_analitica, rel=2e-3)


def test_punto_in_poligono_dentro_e_fuori() -> None:
    poligono = forme.rettangolo(300.0, 500.0)
    assert geometria.punto_in_poligono((0.0, 0.0), poligono)
    assert geometria.punto_in_poligono((149.0, 249.0), poligono)
    assert not geometria.punto_in_poligono((151.0, 0.0), poligono)
    assert not geometria.punto_in_poligono((0.0, 251.0), poligono)


def test_punto_in_poligono_su_bordo_con_tolleranza() -> None:
    poligono = forme.rettangolo(300.0, 500.0)
    assert geometria.punto_in_poligono((150.0, 0.0), poligono, tolleranza_mm=1e-6)


def test_poligono_semplice_rettangolo_vero() -> None:
    assert geometria.poligono_semplice(forme.rettangolo(300.0, 500.0))


def test_poligono_semplice_a_farfalla_falso() -> None:
    farfalla = ((0.0, 0.0), (10.0, 10.0), (10.0, 0.0), (0.0, 10.0))
    assert not geometria.poligono_semplice(farfalla)


def test_normalizza_antiorario_riordina_orario() -> None:
    orario = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0))
    assert geometria.area_con_segno(orario) < 0.0
    antiorario = geometria.normalizza_antiorario(orario)
    assert geometria.area_con_segno(antiorario) > 0.0
    assert geometria.area(antiorario) == pytest.approx(geometria.area(orario))


def test_trasla() -> None:
    poligono = forme.rettangolo(100.0, 100.0)
    traslato = geometria.trasla(poligono, 10.0, -5.0)
    cx, cy = geometria.centroide(traslato)
    assert (cx, cy) == pytest.approx((10.0, -5.0))


def test_ruota_90_gradi_scambia_assi() -> None:
    poligono = forme.rettangolo(200.0, 100.0)  # largo in x, stretto in y
    ruotato = geometria.ruota(poligono, math.pi / 2.0)
    xmin, ymin, xmax, ymax = geometria.bounding_box(ruotato)
    assert (xmax - xmin) == pytest.approx(100.0, abs=1e-9)
    assert (ymax - ymin) == pytest.approx(200.0, abs=1e-9)


def test_taglia_semipiano_rettangolo_a_meta() -> None:
    poligono = forme.rettangolo(200.0, 100.0)
    meta = geometria.taglia_semipiano(poligono, 0.0, 1.0, 0.0)  # keep y <= 0
    assert geometria.area(meta) == pytest.approx(200.0 * 50.0)


@pytest.mark.parametrize("costruttore", [
    lambda: forme.sezione_a_t(400.0, 150.0, 250.0, 600.0),
    lambda: forme.sezione_a_l(400.0, 150.0, 250.0, 600.0),
])
def test_clip_non_convesso_preserva_area_totale(costruttore) -> None:
    """Clipping a non-convex T/L outline (band above + band below the flange line) preserves
    the total area."""
    poligono = costruttore()
    y_giunzione = 600.0 - 150.0
    sopra = geometria.taglia_semipiano(poligono, 0.0, -1.0, y_giunzione)  # keep y >= y_giunzione
    sotto = geometria.taglia_semipiano(poligono, 0.0, 1.0, -y_giunzione)  # keep y <= y_giunzione
    assert geometria.area(sopra) + geometria.area(sotto) == pytest.approx(geometria.area(poligono), rel=1e-9)

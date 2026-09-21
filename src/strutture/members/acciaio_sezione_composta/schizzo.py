"""Live sketch for `acciaio-sezione-h-rimpiattata`: "Sezione" (profile flanges/web plus every
active welded plate as `stile="acciaio"` rectangles, centroid axes, centroid marker) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the already-built `elementi` tuple and the section
centroid; a failure here must never fail the calculation (guarded in `tool.run`)."""
from strutture.shared.sketch import Cerchio, Linea, Rettangolo, Sketch, Vista
from strutture.shared.units import mm_to_m

from .elementi import Elemento

_MARGINE_ASSI = 0.1  # frazione della semi-estensione dell'involucro, oltre l'ingombro degli elementi
_RAGGIO_MARCATORE_MIN_M = 0.003  # raggio minimo del marcatore del baricentro (m)
_RAGGIO_MARCATORE_FRAZIONE = 0.015  # frazione di h_profilo_mm per il raggio del marcatore


def disegna(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float,
            h_profilo_mm: float, b_profilo_mm: float) -> Sketch:
    """Sezione: un rettangolo per ogni elemento (ali, anima, piatti attivi), assi baricentrici e
    marcatore del baricentro."""
    return Sketch(viste=(_sezione(elementi, x_n_mm, y_n_mm, h_profilo_mm, b_profilo_mm),))


def _rettangoli(elementi: tuple[Elemento, ...]) -> tuple[Rettangolo, ...]:
    forme = []
    for elemento in elementi:
        if elemento.b_mm <= 0 or elemento.h_mm <= 0:
            continue  # difensivo: costruisci_elementi filtra già i piatti disattivati
        x = mm_to_m(elemento.x_mm - elemento.b_mm / 2.0)
        y = mm_to_m(elemento.y_mm - elemento.h_mm / 2.0)
        w = mm_to_m(elemento.b_mm)
        h = mm_to_m(elemento.h_mm)
        forme.append(Rettangolo(x=x, y=y, w=w, h=h, stile="acciaio"))
    return tuple(forme)


def _involucro(elementi: tuple[Elemento, ...]) -> tuple[float, float, float, float]:
    """Estremi (x_min, x_max, y_min, y_max) in mm, sull'ingombro di tutti gli elementi."""
    x_min = min(e.x_mm - e.b_mm / 2.0 for e in elementi)
    x_max = max(e.x_mm + e.b_mm / 2.0 for e in elementi)
    y_min = min(e.y_mm - e.h_mm / 2.0 for e in elementi)
    y_max = max(e.y_mm + e.h_mm / 2.0 for e in elementi)
    return x_min, x_max, y_min, y_max


def _assi_baricentrici(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float) -> tuple[Linea, Linea]:
    x_min, x_max, y_min, y_max = _involucro(elementi)
    margine_x = _MARGINE_ASSI * (x_max - x_min)
    margine_y = _MARGINE_ASSI * (y_max - y_min)
    orizzontale = Linea(p1=(mm_to_m(x_min - margine_x), mm_to_m(y_n_mm)),
                         p2=(mm_to_m(x_max + margine_x), mm_to_m(y_n_mm)), stile="asse")
    verticale = Linea(p1=(mm_to_m(x_n_mm), mm_to_m(y_min - margine_y)),
                       p2=(mm_to_m(x_n_mm), mm_to_m(y_max + margine_y)), stile="asse")
    return orizzontale, verticale


def _marcatore_baricentro(x_n_mm: float, y_n_mm: float, h_profilo_mm: float) -> Cerchio:
    raggio = max(_RAGGIO_MARCATORE_MIN_M, _RAGGIO_MARCATORE_FRAZIONE * mm_to_m(h_profilo_mm))
    return Cerchio(centro=(mm_to_m(x_n_mm), mm_to_m(y_n_mm)), r=raggio, stile="asse")


def _sezione(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float,
             h_profilo_mm: float, b_profilo_mm: float) -> Vista:
    orizzontale, verticale = _assi_baricentrici(elementi, x_n_mm, y_n_mm)
    forme = [
        *_rettangoli(elementi),
        orizzontale,
        verticale,
        _marcatore_baricentro(x_n_mm, y_n_mm, h_profilo_mm),
    ]
    return Vista(titolo="Sezione", forme=tuple(forme))

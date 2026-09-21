"""Live sketch for `acciaio-sezione-h-rimpiattata`: "Sezione" (profile flanges/web plus every
active welded plate as `stile="acciaio"` rectangles, centroid axes, centroid marker) —
docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in shared/sketch.py. Pure function of the
already-built `elementi` tuple and the section centroid; a failure here must never fail the
calculation (guarded in `tool.run`).

Welded H sections can be tall/slender (deep custom beams) and their flanges/web are routinely
thinner than 2 % of the section's larger side: the whole section is scaled by `(sx, sy)` to stay
within the readable aspect ratio (rule 1, compresses only the larger side), and every rectangle
then gets a schematic minimum thickness on whichever of its (already scaled) sides is a sliver
(rule 2). Both are visual-only — the real `elementi` (used for the actual section properties) are
never mutated, only their drawn positions/sizes are transformed."""
from strutture.shared.sketch import Cerchio, Linea, Punto, Rettangolo, Sketch, Vista
from strutture.shared.units import mm_to_m

from .elementi import Elemento

_MARGINE_ASSI = 0.1  # frazione della semi-estensione dell'involucro, oltre l'ingombro degli elementi
_RAGGIO_MARCATORE_MIN_M = 0.003  # raggio minimo del marcatore del baricentro (m)
_RAGGIO_MARCATORE_FRAZIONE = 0.015  # frazione di h_profilo_mm per il raggio del marcatore
_ASPETTO_MAX_DISEGNO = 3.0  # margine sotto il limite 3.5:1 del lint di leggibilità (regola 1)
_SPESSORE_MINIMO_FRAZIONE = 0.03  # spessore minimo disegnato di un elemento, frazione del lato maggiore (regola 2)
NOTA_SCHEMA = "Schema non in scala: sezione compressa e/o con spessori minimi schematici per restare leggibile."


def _involucro(elementi: tuple[Elemento, ...]) -> tuple[float, float, float, float]:
    """Estremi (x_min, x_max, y_min, y_max) in mm, sull'ingombro di tutti gli elementi."""
    x_min = min(e.x_mm - e.b_mm / 2.0 for e in elementi)
    x_max = max(e.x_mm + e.b_mm / 2.0 for e in elementi)
    y_min = min(e.y_mm - e.h_mm / 2.0 for e in elementi)
    y_max = max(e.y_mm + e.h_mm / 2.0 for e in elementi)
    return x_min, x_max, y_min, y_max


def _fattori_scala(larghezza_mm: float, altezza_mm: float) -> tuple[float, float]:
    """(sx, sy): il lato maggiore è compresso quando l'aspetto della sezione supera il leggibile."""
    maggiore, minore = max(larghezza_mm, altezza_mm), min(larghezza_mm, altezza_mm)
    if minore <= 0 or maggiore / minore <= _ASPETTO_MAX_DISEGNO:
        return 1.0, 1.0
    fattore = _ASPETTO_MAX_DISEGNO * minore / maggiore
    return (fattore, 1.0) if larghezza_mm >= altezza_mm else (1.0, fattore)


def _punto(x_mm: float, y_mm: float, sx: float, sy: float) -> Punto:
    return mm_to_m(x_mm * sx), mm_to_m(y_mm * sy)


def disegna(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float,
            h_profilo_mm: float, b_profilo_mm: float) -> Sketch:
    """Sezione: un rettangolo per ogni elemento (ali, anima, piatti attivi), assi baricentrici e
    marcatore del baricentro."""
    x_min, x_max, y_min, y_max = _involucro(elementi)
    sx, sy = _fattori_scala(x_max - x_min, y_max - y_min)
    vista, spessori_minimi_usati = _sezione(elementi, x_n_mm, y_n_mm, h_profilo_mm, sx, sy)
    nota = NOTA_SCHEMA if (sx, sy) != (1.0, 1.0) or spessori_minimi_usati else ""
    return Sketch(viste=(vista,), nota=nota)


def _rettangoli(elementi: tuple[Elemento, ...], sx: float, sy: float, maggiore_disegnato_m: float) -> tuple[tuple[Rettangolo, ...], bool]:
    minimo_m = _SPESSORE_MINIMO_FRAZIONE * maggiore_disegnato_m
    forme: list[Rettangolo] = []
    usato_minimo = False
    for elemento in elementi:
        if elemento.b_mm <= 0 or elemento.h_mm <= 0:
            continue  # difensivo: costruisci_elementi filtra già i piatti disattivati
        cx_m, cy_m = mm_to_m(elemento.x_mm * sx), mm_to_m(elemento.y_mm * sy)
        w_m, h_m = mm_to_m(elemento.b_mm * sx), mm_to_m(elemento.h_mm * sy)
        if w_m < minimo_m:
            w_m, usato_minimo = minimo_m, True
        if h_m < minimo_m:
            h_m, usato_minimo = minimo_m, True
        forme.append(Rettangolo(x=cx_m - w_m / 2.0, y=cy_m - h_m / 2.0, w=w_m, h=h_m, stile="acciaio"))
    return tuple(forme), usato_minimo


def _assi_baricentrici(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float, sx: float, sy: float) -> tuple[Linea, Linea]:
    x_min, x_max, y_min, y_max = _involucro(elementi)
    margine_x = _MARGINE_ASSI * (x_max - x_min)
    margine_y = _MARGINE_ASSI * (y_max - y_min)
    y_n_m = _punto(0.0, y_n_mm, sx, sy)[1]
    x_n_m = _punto(x_n_mm, 0.0, sx, sy)[0]
    orizzontale = Linea(p1=(_punto(x_min - margine_x, 0.0, sx, sy)[0], y_n_m),
                         p2=(_punto(x_max + margine_x, 0.0, sx, sy)[0], y_n_m), stile="asse")
    verticale = Linea(p1=(x_n_m, _punto(0.0, y_min - margine_y, sx, sy)[1]),
                       p2=(x_n_m, _punto(0.0, y_max + margine_y, sx, sy)[1]), stile="asse")
    return orizzontale, verticale


def _marcatore_baricentro(x_n_mm: float, y_n_mm: float, h_profilo_mm: float, sx: float, sy: float) -> Cerchio:
    raggio = max(_RAGGIO_MARCATORE_MIN_M, _RAGGIO_MARCATORE_FRAZIONE * mm_to_m(h_profilo_mm))
    return Cerchio(centro=_punto(x_n_mm, y_n_mm, sx, sy), r=raggio, stile="asse")


def _sezione(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float, h_profilo_mm: float,
             sx: float, sy: float) -> tuple[Vista, bool]:
    x_min, x_max, y_min, y_max = _involucro(elementi)
    maggiore_disegnato_m = max(mm_to_m((x_max - x_min) * sx), mm_to_m((y_max - y_min) * sy))
    rettangoli, spessori_minimi_usati = _rettangoli(elementi, sx, sy, maggiore_disegnato_m)
    orizzontale, verticale = _assi_baricentrici(elementi, x_n_mm, y_n_mm, sx, sy)
    forme = [
        *rettangoli,
        orizzontale,
        verticale,
        _marcatore_baricentro(x_n_mm, y_n_mm, h_profilo_mm, sx, sy),
    ]
    return Vista(titolo="Sezione", forme=tuple(forme)), spessori_minimi_usati

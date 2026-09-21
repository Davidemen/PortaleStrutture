"""Live sketch for `ca-mensola-tozza`: "Prospetto" (column, tapered corbel wedge, load arrow,
strut-and-tie lines, a/h dimensions, b label) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the
validated inputs + the geometry result; a failure here must never fail the calculation (guarded in
`tool.run`)."""
from strutture.shared.sketch import (
    Etichetta,
    Freccia,
    Linea,
    Poligono,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    etichetta_quota,
)
from strutture.shared.units import mm_to_m

from .models import GeometriaResult, MensolaTozzaInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
# La larghezza del pilastro non è un input del tool: si assume una proporzione puramente
# illustrativa, che non influenza alcun calcolo.
_PROPORZIONE_COLONNA = 0.9  # larghezza colonna = 0.9 * h_mm
_ESTENSIONE_COLONNA_INF = 0.5  # tratto di colonna disegnato sotto la mensola, frazione di h_mm
_ESTENSIONE_COLONNA_SUP = 2.0  # tratto di colonna disegnato sopra la mensola, frazione di h_mm
_ALTEZZA_FRECCIA_CARICO = 0.4  # coda della freccia di carico sopra il punto di applicazione, frazione di h_mm
_OFFSET_ETICHETTA_B = 0.05  # scostamento dell'etichetta "b" dal vertice della mensola, frazione di h_mm


def disegna(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Sketch:
    """Prospetto della mensola sul filo del pilastro, con le bielle del modello a traliccio."""
    return Sketch(viste=(_prospetto(inputs, geometria),))


def _colonna(inputs: MensolaTozzaInput) -> Rettangolo:
    """Pilastro schematico dietro la mensola, a proporzione illustrativa fissa."""
    larghezza_m = mm_to_m(_PROPORZIONE_COLONNA * inputs.h_mm)
    y0_m = mm_to_m(-_ESTENSIONE_COLONNA_INF * inputs.h_mm)
    altezza_m = mm_to_m((_ESTENSIONE_COLONNA_INF + _ESTENSIONE_COLONNA_SUP) * inputs.h_mm)
    return Rettangolo(x=-larghezza_m, y=y0_m, w=larghezza_m, h=altezza_m, stile="calcestruzzo")


def _mensola(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Poligono:
    """Cuneo dal filo del pilastro (altezza piena h) al punto di carico (altezza d)."""
    punti = (
        (0.0, 0.0),
        (mm_to_m(inputs.a_mm), 0.0),
        (mm_to_m(inputs.a_mm), mm_to_m(geometria.d_mm)),
        (0.0, mm_to_m(inputs.h_mm)),
    )
    return Poligono(punti=punti, stile="calcestruzzo")


def _punto_carico_m(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> tuple[float, float]:
    return mm_to_m(inputs.a_mm), mm_to_m(geometria.d_mm)


def _carico(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Freccia:
    x_m, y_m = _punto_carico_m(inputs, geometria)
    coda = (x_m, y_m + mm_to_m(_ALTEZZA_FRECCIA_CARICO * inputs.h_mm))
    return Freccia(coda=coda, punta=(x_m, y_m), testo=etichetta_quota("P_Ed", inputs.ped_kN, "kN", 0), stile="carico")


def _puntone(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Linea:
    """Biella compressa, dal punto di carico al nodo inferiore sul filo del pilastro."""
    nodo = (0.0, mm_to_m(inputs.c_mm))
    return Linea(p1=_punto_carico_m(inputs, geometria), p2=nodo, stile="puntone")


def _tirante(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Linea:
    """Tirante teso, dal punto di carico al nodo superiore sul filo del pilastro."""
    nodo = (0.0, mm_to_m(inputs.h_mm - inputs.c_mm))
    return Linea(p1=_punto_carico_m(inputs, geometria), p2=nodo, stile="tirante")


def _quote(inputs: MensolaTozzaInput) -> tuple[Quota, Quota]:
    a_m, h_m = mm_to_m(inputs.a_mm), mm_to_m(inputs.h_mm)
    scostamento = _MARGINE_QUOTA * max(a_m, h_m)
    quota_a = Quota(p1=(0.0, 0.0), p2=(a_m, 0.0), distanza=-scostamento,
                     testo=etichetta_quota("a", inputs.a_mm, "mm", 0))
    # h si misura sul filo del pilastro (x = 0); la linea di quota va a DESTRA, oltre la punta della mensola:
    # a sinistra cadrebbe dentro il pilastro (convenzione dei lati: vedi shared/sketch.py).
    quota_h = Quota(p1=(0.0, 0.0), p2=(0.0, h_m), distanza=-(a_m + scostamento),
                     testo=etichetta_quota("h", inputs.h_mm, "mm", 0))
    return quota_a, quota_h


def _etichetta_b(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Etichetta:
    """`b` non è quotabile in un prospetto (è la dimensione fuori piano): un'etichetta vicino
    all'apice della mensola."""
    x_m, y_m = _punto_carico_m(inputs, geometria)
    offset_m = mm_to_m(_OFFSET_ETICHETTA_B * inputs.h_mm)
    return Etichetta(punto=(x_m + offset_m, y_m + offset_m), simbolo="b",
                      testo=etichetta_quota("b", inputs.b_mm, "mm", 0))


def _prospetto(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Vista:
    quota_a, quota_h = _quote(inputs)
    forme = (
        _colonna(inputs),
        _mensola(inputs, geometria),
        _carico(inputs, geometria),
        _puntone(inputs, geometria),
        _tirante(inputs, geometria),
        quota_a,
        quota_h,
        _etichetta_b(inputs, geometria),
    )
    return Vista(titolo="Prospetto", forme=forme)

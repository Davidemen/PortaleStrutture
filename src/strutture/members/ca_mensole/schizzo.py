"""Live sketch for `ca-mensola-tozza`: "Prospetto" (column with `fantasma`-continued ends, tapered
corbel wedge, load arrow, strut-and-tie lines, a/h dimensions) — docs/ui/WORKBENCH_SPEC.md §7,
COMPOSITION RULES in shared/sketch.py. Pure function of the validated inputs + the geometry
result; a failure here must never fail the calculation (guarded in `tool.run`).

Design review fixes: the column is now a modest, schematic slice around the corbel (not a
3.5·h tower) with dashed `fantasma` stubs at both ends to show it continues; `a` gets a schematic
minimum of 0.6·h so a very short corbel doesn't collapse into the column (the quota still reports
the true `a`, `Sketch.nota` says so); the `P_Ed` label sits above the arrow's tail; the `b` label
was dropped (`b` is the out-of-plane width, meaningless in an elevation)."""
from strutture.shared.sketch import (
    Etichetta,
    Freccia,
    Linea,
    Poligono,
    Punto,
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
_PROPORZIONE_COLONNA = 0.5  # larghezza colonna = 0.5 * h_mm
_ESTENSIONE_COLONNA_INF = 0.4  # tratto di colonna disegnato sotto la mensola, frazione di h_mm
_ESTENSIONE_COLONNA_SUP = 0.6  # tratto di colonna disegnato sopra la mensola, frazione di h_mm
_FANTASMA_COLONNA_FRAZIONE = 0.2  # lunghezza dei tratti "fantasma" alle due estremità, frazione dell'altezza disegnata
_ALTEZZA_FRECCIA_CARICO = 0.4  # coda della freccia di carico sopra il punto di applicazione, frazione di h_mm
_OFFSET_ETICHETTA_PED = 0.12  # scostamento dell'etichetta P_Ed sopra la coda della freccia, frazione di h_mm
_A_MINIMO_SU_H = 0.6  # scostamento minimo schematico di a dal filo del pilastro, frazione di h_mm
NOTA_A_MINIMO = "Schema non in scala: a disegnata con uno scostamento minimo leggibile dal pilastro."


def disegna(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Sketch:
    """Prospetto della mensola sul filo del pilastro, con le bielle del modello a traliccio."""
    a_disegnato_mm = max(inputs.a_mm, _A_MINIMO_SU_H * inputs.h_mm)
    nota = NOTA_A_MINIMO if a_disegnato_mm > inputs.a_mm else ""
    return Sketch(viste=(_prospetto(inputs, geometria, a_disegnato_mm),), nota=nota)


def _colonna(inputs: MensolaTozzaInput) -> tuple[Rettangolo, Linea, Linea]:
    """Pilastro schematico dietro la mensola, a proporzione illustrativa fissa, con tratti
    "fantasma" tratteggiati alle due estremità a indicare che il pilastro reale continua oltre."""
    larghezza_m = mm_to_m(_PROPORZIONE_COLONNA * inputs.h_mm)
    y0_m = mm_to_m(-_ESTENSIONE_COLONNA_INF * inputs.h_mm)
    altezza_m = mm_to_m((_ESTENSIONE_COLONNA_INF + _ESTENSIONE_COLONNA_SUP) * inputs.h_mm)
    rettangolo = Rettangolo(x=-larghezza_m, y=y0_m, w=larghezza_m, h=altezza_m, stile="calcestruzzo")
    x_centro_m = -larghezza_m / 2.0
    tratto_m = _FANTASMA_COLONNA_FRAZIONE * altezza_m
    fantasma_inf = Linea(p1=(x_centro_m, y0_m), p2=(x_centro_m, y0_m - tratto_m), stile="fantasma", tratteggio=True)
    fantasma_sup = Linea(p1=(x_centro_m, y0_m + altezza_m), p2=(x_centro_m, y0_m + altezza_m + tratto_m),
                          stile="fantasma", tratteggio=True)
    return rettangolo, fantasma_inf, fantasma_sup


def _mensola(inputs: MensolaTozzaInput, geometria: GeometriaResult, a_disegnato_mm: float) -> Poligono:
    """Cuneo dal filo del pilastro (altezza piena h) al punto di carico (altezza d)."""
    punti = (
        (0.0, 0.0),
        (mm_to_m(a_disegnato_mm), 0.0),
        (mm_to_m(a_disegnato_mm), mm_to_m(geometria.d_mm)),
        (0.0, mm_to_m(inputs.h_mm)),
    )
    return Poligono(punti=punti, stile="calcestruzzo")


def _punto_carico_m(geometria: GeometriaResult, a_disegnato_mm: float) -> Punto:
    return mm_to_m(a_disegnato_mm), mm_to_m(geometria.d_mm)


def _freccia_carico(inputs: MensolaTozzaInput, geometria: GeometriaResult, a_disegnato_mm: float) -> Freccia:
    """Freccia del carico verticale, senza testo proprio: l'etichetta P_Ed è un'`Etichetta`
    separata, ancorata sopra la coda (regola 4: `testo` è già impostato via `simbolo`)."""
    x_m, y_m = _punto_carico_m(geometria, a_disegnato_mm)
    coda_m = (x_m, y_m + mm_to_m(_ALTEZZA_FRECCIA_CARICO * inputs.h_mm))
    return Freccia(coda=coda_m, punta=(x_m, y_m), stile="carico")


def _etichetta_ped(inputs: MensolaTozzaInput, coda: Punto) -> Etichetta:
    """Etichetta P_Ed sopra la coda della freccia (non sulla coda stessa, per non sovrapporsi)."""
    punto_sopra = (coda[0], coda[1] + mm_to_m(_OFFSET_ETICHETTA_PED * inputs.h_mm))
    numero = f"{inputs.ped_kN:.0f}".replace(".", ",")
    return Etichetta(punto=punto_sopra, simbolo="P_Ed", testo=f"{numero} kN", ancora="middle", stile="asse")


def _puntone(geometria: GeometriaResult, inputs: MensolaTozzaInput, a_disegnato_mm: float) -> Linea:
    """Biella compressa, dal punto di carico al nodo inferiore sul filo del pilastro."""
    nodo = (0.0, mm_to_m(inputs.c_mm))
    return Linea(p1=_punto_carico_m(geometria, a_disegnato_mm), p2=nodo, stile="puntone")


def _tirante(geometria: GeometriaResult, inputs: MensolaTozzaInput, a_disegnato_mm: float) -> Linea:
    """Tirante teso, dal punto di carico al nodo superiore sul filo del pilastro."""
    nodo = (0.0, mm_to_m(inputs.h_mm - inputs.c_mm))
    return Linea(p1=_punto_carico_m(geometria, a_disegnato_mm), p2=nodo, stile="tirante")


def _quote(inputs: MensolaTozzaInput, a_disegnato_mm: float) -> tuple[Quota, Quota]:
    a_m, h_m = mm_to_m(a_disegnato_mm), mm_to_m(inputs.h_mm)
    scostamento = _MARGINE_QUOTA * max(a_m, h_m)
    quota_a = Quota(p1=(0.0, 0.0), p2=(a_m, 0.0), distanza=-scostamento,
                     testo=etichetta_quota("a", inputs.a_mm, "mm", 0))
    # h si misura sul filo del pilastro (x = 0); la linea di quota va a DESTRA, oltre la punta della mensola:
    # a sinistra cadrebbe dentro il pilastro (convenzione dei lati: vedi shared/sketch.py).
    quota_h = Quota(p1=(0.0, 0.0), p2=(0.0, h_m), distanza=-(a_m + scostamento),
                     testo=etichetta_quota("h", inputs.h_mm, "mm", 0))
    return quota_a, quota_h


def _prospetto(inputs: MensolaTozzaInput, geometria: GeometriaResult, a_disegnato_mm: float) -> Vista:
    rettangolo, fantasma_inf, fantasma_sup = _colonna(inputs)
    quota_a, quota_h = _quote(inputs, a_disegnato_mm)
    freccia = _freccia_carico(inputs, geometria, a_disegnato_mm)
    forme = (
        rettangolo,
        fantasma_inf,
        fantasma_sup,
        _mensola(inputs, geometria, a_disegnato_mm),
        freccia,
        _etichetta_ped(inputs, freccia.coda),
        _puntone(geometria, inputs, a_disegnato_mm),
        _tirante(geometria, inputs, a_disegnato_mm),
        quota_a,
        quota_h,
    )
    return Vista(titolo="Prospetto", forme=forme)

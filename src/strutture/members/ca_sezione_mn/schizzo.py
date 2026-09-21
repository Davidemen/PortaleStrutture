"""Live sketch for `ca-sezione-dominio-mn`: section outline + bars + the neutral axis of the
governing combination (docs/ui/WORKBENCH_SPEC.md §7, `shared/sketch.py` composition rules). Pure
function of the validated inputs + computed results; a failure here must never fail the calculation
(guarded in `compose.run`, same pattern as `ca_punzonamento.schizzo`)."""
import math

from strutture.shared.sezione_ca.geometria import bounding_box
from strutture.shared.sezione_ca.modelli import Sezione
from strutture.shared.sketch import Barre, Etichetta, Linea, Poligono, Sketch, Vista
from strutture.shared.units import mm_to_m

from .assi_neutri import PianoDeformazione

_MARGINE_ETICHETTA_FATTORE = 0.06  # scostamento dell'etichetta "Asse neutro" dal bordo sezione, frazione del lato maggiore.


_NOTA_FUORI_DOMINIO = "N_Ed della combinazione governante fuori dal dominio di resistenza: asse neutro non disegnato."
_NOTA_STATO_UNIFORME = "Combinazione governante in compressione o trazione pura: asse neutro non definito."


def disegna(sezione: Sezione, piano_asse_neutro: PianoDeformazione | None) -> Sketch:
    """Pianta della sezione: contorno in cls, barre (raggruppate per diametro) e l'asse neutro
    della combinazione governante, se questa è interna al dominio di resistenza e lo stato non è di
    compressione/trazione uniforme (curvatura nulla, nessun asse neutro da disegnare — `_asse_neutro`
    torna `None` anche in quel caso, non solo quando `piano_asse_neutro` è `None`: entrambi i casi
    lasciano una nota esplicita, mai un disegno silenziosamente incompleto)."""
    forme = [_contorno(sezione), *_barre(sezione)]
    linea = None if piano_asse_neutro is None else _asse_neutro(sezione, piano_asse_neutro)
    if linea is not None:
        forme = [*forme, linea, _etichetta_asse_neutro(sezione, linea)]
        nota = ""
    else:
        nota = _NOTA_FUORI_DOMINIO if piano_asse_neutro is None else _NOTA_STATO_UNIFORME
    return Sketch(viste=(Vista(titolo="Sezione", forme=tuple(forme)),), nota=nota)


def _contorno(sezione: Sezione) -> Poligono:
    return Poligono(punti=tuple((mm_to_m(x), mm_to_m(y)) for x, y in sezione.contorno), stile="calcestruzzo")


def _barre(sezione: Sezione) -> tuple[Barre, ...]:
    """Una forma `Barre` per ogni diametro distinto (il widget disegna un diametro uniforme)."""
    diametri = sorted({barra.diametro_mm for barra in sezione.barre})
    return tuple(
        Barre(
            centri=tuple((mm_to_m(b.x_mm), mm_to_m(b.y_mm)) for b in sezione.barre if b.diametro_mm == diametro),
            diametro=mm_to_m(diametro), stile="armatura",
        )
        for diametro in diametri
    )


def _clip_a_bbox(p0: tuple[float, float], d: tuple[float, float], bbox: tuple[float, float, float, float]) -> tuple[float, float] | None:
    xmin, ymin, xmax, ymax = bbox
    s_lo, s_hi = -math.inf, math.inf
    for p0_c, d_c, lo, hi in ((p0[0], d[0], xmin, xmax), (p0[1], d[1], ymin, ymax)):
        if d_c == 0.0:
            if not lo <= p0_c <= hi:
                return None
            continue
        s1, s2 = (lo - p0_c) / d_c, (hi - p0_c) / d_c
        s_lo, s_hi = max(s_lo, min(s1, s2)), min(s_hi, max(s1, s2))
    return None if s_lo > s_hi else (s_lo, s_hi)


def _asse_neutro(sezione: Sezione, piano: PianoDeformazione) -> Linea | None:
    """La retta ε(x,y) = 0, cioè `kx*y - ky*x + eps0 = 0`, tagliata al riquadro della sezione."""
    eps0, kx, ky = piano
    if kx == 0.0 and ky == 0.0:
        return None
    direzione = (kx, ky)
    punto = (0.0, -eps0 / kx) if kx != 0.0 else (eps0 / ky, 0.0)
    bbox_mm = bounding_box(sezione.contorno)
    intervallo = _clip_a_bbox(punto, direzione, bbox_mm)
    if intervallo is None:
        return None
    s_lo, s_hi = intervallo
    p1 = (mm_to_m(punto[0] + s_lo * direzione[0]), mm_to_m(punto[1] + s_lo * direzione[1]))
    p2 = (mm_to_m(punto[0] + s_hi * direzione[0]), mm_to_m(punto[1] + s_hi * direzione[1]))
    return Linea(p1=p1, p2=p2, stile="asse", tratteggio=True)


def _etichetta_asse_neutro(sezione: Sezione, linea: Linea) -> Etichetta:
    xmin, ymin, xmax, ymax = bounding_box(sezione.contorno)
    lato_maggiore_m = mm_to_m(max(xmax - xmin, ymax - ymin))
    punto = (linea.p2[0], linea.p2[1] + _MARGINE_ETICHETTA_FATTORE * lato_maggiore_m)
    return Etichetta(punto=punto, testo="Asse neutro", ancora="end", stile="asse")

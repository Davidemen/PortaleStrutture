"""Live sketch for `ca-taglio-non-armato`: "Sezione" (concrete outline, tension-bar row at the
effective depth, b/d dimensions) — docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in
shared/sketch.py. Pure function of the validated inputs + the geometry result; a failure here must
never fail the calculation (guarded in `compose.run`).

This tool is often used on a 1 m-wide strip with `bw_mm` far larger than `h_mm` (e.g. `bw_mm=1000`
per the sheet's own convention): the wider side is compressed to stay within the readable aspect
ratio (rule 1), scaling only the x-coordinates (bar positions, rectangle width); bar diameters and
dimension texts always use the true input values."""
import math

from strutture.shared.sketch import Barre, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import GeometriaOutput, TaglioNonArmatoInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_ASPETTO_MAX_DISEGNO = 3.0  # margine sotto il limite 3.5:1 del lint di leggibilità (regola 1)

# Diametro solo per il disegno quando Asl e' nota come area diretta (nessun N°/Ø in input):
# non entra in nessun calcolo, serve solo a stimare quante barre "illustrative" disegnare.
DIAMETRO_ILLUSTRATIVO_MM = 16.0

_NOTA_DIAMETRO_ILLUSTRATIVO = (
    "Diametro delle barre illustrativo (Asl inserita direttamente, senza N° e Ø): non rappresenta "
    "un diametro commerciale reale e non è usato in alcun calcolo."
)
_NOTA_SCHEMA = "Schema non in scala: sezione compressa sul lato maggiore per restare leggibile."


def _fattori_scala(b_mm: float, h_mm: float) -> tuple[float, float]:
    """(sx, sy): il lato maggiore è compresso quando il rapporto b/h supera l'aspetto leggibile."""
    maggiore, minore = max(b_mm, h_mm), min(b_mm, h_mm)
    if minore <= 0 or maggiore / minore <= _ASPETTO_MAX_DISEGNO:
        return 1.0, 1.0
    fattore = _ASPETTO_MAX_DISEGNO * minore / maggiore
    return (fattore, 1.0) if b_mm >= h_mm else (1.0, fattore)


def _punto(x_mm: float, y_mm: float, sx: float, sy: float) -> Punto:
    return mm_to_m(x_mm * sx), mm_to_m(y_mm * sy)


def disegna(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> Sketch:
    """Sezione b×d della sezione priva di armatura trasversale, con la riga di barre tese."""
    illustrativo = inputs.n_barre is None or inputs.diametro_barre_mm is None
    sx, sy = _fattori_scala(inputs.bw_mm, inputs.h_mm)
    compresso = (sx, sy) != (1.0, 1.0)
    note = [n for n in (_NOTA_DIAMETRO_ILLUSTRATIVO if illustrativo else "", _NOTA_SCHEMA if compresso else "") if n]
    return Sketch(viste=(_sezione(inputs, geometria, sx, sy),), nota=" ".join(note))


def _bar_positions_mm(n: int, b_mm: float, copriferro_mm: float) -> tuple[float, ...]:
    """Ascisse (mm, non scalate) delle barre, distribuite tra i due copriferri laterali."""
    if n <= 1:
        return (b_mm / 2.0,)
    passo_mm = (b_mm - 2.0 * copriferro_mm) / (n - 1)
    return tuple(copriferro_mm + i * passo_mm for i in range(n))


def _barre_tese(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput, sx: float, sy: float) -> Barre:
    n, diametro_mm, illustrativo = _n_e_diametro(inputs, geometria)
    xs_mm = _bar_positions_mm(n, inputs.bw_mm, inputs.c_mm)
    centri = tuple(_punto(x_mm, inputs.c_mm, sx, sy) for x_mm in xs_mm)
    stile = "fantasma" if illustrativo else "armatura"
    return Barre(centri=centri, diametro=mm_to_m(diametro_mm), stile=stile)


def _n_e_diametro(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> tuple[int, float, bool]:
    """Barre da disegnare: diametro vero se N°/Ø sono stati dati in input, altrimenti un numero di
    barre stimato dal diametro illustrativo fisso a partire dall'area Asl risolta (terzo valore:
    True se il diametro è illustrativo, non un dato vero)."""
    if inputs.n_barre is not None and inputs.diametro_barre_mm is not None:
        return inputs.n_barre, inputs.diametro_barre_mm, False
    area_barra_mm2 = math.pi / 4.0 * DIAMETRO_ILLUSTRATIVO_MM**2
    n = max(1, round(geometria.asl_mm2 / area_barra_mm2))
    return n, DIAMETRO_ILLUSTRATIVO_MM, True


def _quote(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput, sx: float, sy: float) -> tuple[Quota, Quota]:
    b_m, h_m = mm_to_m(inputs.bw_mm * sx), mm_to_m(inputs.h_mm * sy)
    c_m = mm_to_m(inputs.c_mm * sy)
    scostamento = _MARGINE_QUOTA * max(b_m, h_m)
    quota_b = Quota(p1=(0.0, 0.0), p2=(b_m, 0.0), distanza=-scostamento,
                     testo=etichetta_quota("b", inputs.bw_mm, "mm", 0), campo="bw_mm")
    # d misurato dal lembo compresso (sommita') fino alla riga di barre tese, non l'altezza h intera.
    # p1 -> p2 scende lungo il lato sinistro: la sinistra del segmento e' l'INTERNO della sezione, quindi distanza negativa.
    quota_d = Quota(p1=(0.0, h_m), p2=(0.0, c_m), distanza=-scostamento,
                     testo=etichetta_quota("d", geometria.d_mm, "mm", 0), campo="h_mm")  # d = h − c: si modifica h
    return quota_b, quota_d


def _sezione(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput, sx: float, sy: float) -> Vista:
    b_m, h_m = mm_to_m(inputs.bw_mm * sx), mm_to_m(inputs.h_mm * sy)
    quota_b, quota_d = _quote(inputs, geometria, sx, sy)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=b_m, h=h_m, stile="calcestruzzo"),
        _barre_tese(inputs, geometria, sx, sy),
        quota_b,
        quota_d,
    ]
    return Vista(titolo="Sezione", forme=tuple(forme))

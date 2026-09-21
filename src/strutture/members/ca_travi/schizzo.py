"""Live sketch for `ca-trave-rettangolare`: "Sezione" (concrete outline, stirrup outline, tension
and compression bars at true diameter, neutral-axis line, b/h dimensions) —
docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in shared/sketch.py. Pure function of the
validated inputs + the flexural ULS result; a failure here must never fail the calculation
(guarded in `tool.run`).

Very wide/shallow or narrow/deep sections are compressed on their longer side to stay within the
readable aspect ratio (rule 1): every coordinate is scaled by `(sx, sy)` (bar/stirrup positions,
the neutral-axis line), but bar DIAMETERS and dimension TEXTS always use the true input values."""
from strutture.shared.sketch import Barre, Linea, Poligono, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import FlessioneOutput, TraveRettangolareInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_ASPETTO_MAX_DISEGNO = 3.0  # margine sotto il limite 3.5:1 del lint di leggibilità (regola 1)
NOTA_SCHEMA = "Schema non in scala: sezione compressa sul lato maggiore per restare leggibile."


def _fattori_scala(b_mm: float, h_mm: float) -> tuple[float, float]:
    """(sx, sy): il lato maggiore è compresso quando il rapporto b/h supera l'aspetto leggibile."""
    maggiore, minore = max(b_mm, h_mm), min(b_mm, h_mm)
    if minore <= 0 or maggiore / minore <= _ASPETTO_MAX_DISEGNO:
        return 1.0, 1.0
    fattore = _ASPETTO_MAX_DISEGNO * minore / maggiore
    return (fattore, 1.0) if b_mm >= h_mm else (1.0, fattore)


def _punto(x_mm: float, y_mm: float, sx: float, sy: float) -> Punto:
    return mm_to_m(x_mm * sx), mm_to_m(y_mm * sy)


def disegna(inputs: TraveRettangolareInput, flessione: FlessioneOutput) -> Sketch:
    """Sezione b×h della trave, sotto la combinazione di progetto a flessione."""
    sx, sy = _fattori_scala(inputs.b_mm, inputs.h_mm)
    nota = NOTA_SCHEMA if (sx, sy) != (1.0, 1.0) else ""
    return Sketch(viste=(_sezione(inputs, flessione, sx, sy),), nota=nota)


def _bar_positions_mm(n: int, b_mm: float, copriferro_mm: float) -> tuple[float, ...]:
    """Ascisse (mm, non scalate) delle barre di uno strato, tra i due copriferri laterali."""
    if n <= 1:
        return (b_mm / 2.0,)
    passo_mm = (b_mm - 2.0 * copriferro_mm) / (n - 1)
    return tuple(copriferro_mm + i * passo_mm for i in range(n))


def _staffa(inputs: TraveRettangolareInput, sx: float, sy: float) -> Poligono:
    """Rettangolo (in poligono) della gabbia di staffe, appena dentro il copriferro."""
    inset_mm = inputs.copriferro_mm - inputs.diametro_staffe1_mm / 2.0
    p0 = _punto(inset_mm, inset_mm, sx, sy)
    p1 = _punto(inputs.b_mm - inset_mm, inset_mm, sx, sy)
    p2 = _punto(inputs.b_mm - inset_mm, inputs.h_mm - inset_mm, sx, sy)
    p3 = _punto(inset_mm, inputs.h_mm - inset_mm, sx, sy)
    return Poligono(punti=(p0, p1, p2, p3), stile="armatura")


def _barre_tese(inputs: TraveRettangolareInput, sx: float, sy: float) -> Barre:
    xs_mm = _bar_positions_mm(inputs.n_ferri1, inputs.b_mm, inputs.copriferro_mm)
    centri = tuple(_punto(x_mm, inputs.copriferro_mm, sx, sy) for x_mm in xs_mm)
    return Barre(centri=centri, diametro=mm_to_m(inputs.diametro_ferri1_mm), stile="armatura")


def _barre_compresse(inputs: TraveRettangolareInput, sx: float, sy: float) -> Barre | None:
    if inputs.n_ferri2 <= 0:
        return None
    xs_mm = _bar_positions_mm(inputs.n_ferri2, inputs.b_mm, inputs.copriferro_mm)
    y_mm = inputs.h_mm - inputs.copriferro_mm
    centri = tuple(_punto(x_mm, y_mm, sx, sy) for x_mm in xs_mm)
    return Barre(centri=centri, diametro=mm_to_m(inputs.diametro_ferri2_mm), stile="armatura")


def _asse_neutro(inputs: TraveRettangolareInput, flessione: FlessioneOutput, sx: float, sy: float) -> Linea:
    """Profondità x dell'asse neutro, misurata dal lembo compresso (superiore)."""
    y_mm = inputs.h_mm - flessione.y_mm
    p1 = _punto(0.0, y_mm, sx, sy)
    p2 = _punto(inputs.b_mm, y_mm, sx, sy)
    return Linea(p1=p1, p2=p2, stile="evidenza", tratteggio=True)


def _quote(inputs: TraveRettangolareInput, sx: float, sy: float) -> tuple[Quota, Quota]:
    b_m, h_m = mm_to_m(inputs.b_mm * sx), mm_to_m(inputs.h_mm * sy)
    scostamento = _MARGINE_QUOTA * max(b_m, h_m)
    quota_b = Quota(p1=(0.0, 0.0), p2=(b_m, 0.0), distanza=-scostamento, testo=etichetta_quota("b", inputs.b_mm, "mm", 0))
    quota_h = Quota(p1=(0.0, 0.0), p2=(0.0, h_m), distanza=scostamento, testo=etichetta_quota("h", inputs.h_mm, "mm", 0))
    return quota_b, quota_h


def _sezione(inputs: TraveRettangolareInput, flessione: FlessioneOutput, sx: float, sy: float) -> Vista:
    b_m, h_m = mm_to_m(inputs.b_mm * sx), mm_to_m(inputs.h_mm * sy)
    quota_b, quota_h = _quote(inputs, sx, sy)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=b_m, h=h_m, stile="calcestruzzo"),
        _staffa(inputs, sx, sy),
        _barre_tese(inputs, sx, sy),
    ]
    compresse = _barre_compresse(inputs, sx, sy)
    if compresse is not None:
        forme.append(compresse)
    forme.append(_asse_neutro(inputs, flessione, sx, sy))
    forme.append(quota_b)
    forme.append(quota_h)
    return Vista(titolo="Sezione", forme=tuple(forme))

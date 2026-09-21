"""Live sketch for `ca-trave-rettangolare`: "Sezione" (concrete outline, stirrup outline, tension
and compression bars at true diameter, neutral-axis line, b/h dimensions) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + the flexural ULS result; a
failure here must never fail the calculation (guarded in `tool.run`)."""
from strutture.shared.sketch import Barre, Linea, Poligono, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import FlessioneOutput, TraveRettangolareInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota


def disegna(inputs: TraveRettangolareInput, flessione: FlessioneOutput) -> Sketch:
    """Sezione b×h della trave, sotto la combinazione di progetto a flessione."""
    return Sketch(viste=(_sezione(inputs, flessione),))


def _bar_positions_m(n: int, b_mm: float, copriferro_mm: float) -> tuple[float, ...]:
    """Ascisse delle barre di uno strato, distribuite tra i due copriferri laterali."""
    if n <= 1:
        return (mm_to_m(b_mm / 2.0),)
    passo_mm = (b_mm - 2.0 * copriferro_mm) / (n - 1)
    return tuple(mm_to_m(copriferro_mm + i * passo_mm) for i in range(n))


def _staffa(inputs: TraveRettangolareInput) -> Poligono:
    """Rettangolo (in poligono) della gabbia di staffe, appena dentro il copriferro."""
    inset_mm = inputs.copriferro_mm - inputs.diametro_staffe1_mm / 2.0
    x0, y0 = mm_to_m(inset_mm), mm_to_m(inset_mm)
    x1, y1 = mm_to_m(inputs.b_mm - inset_mm), mm_to_m(inputs.h_mm - inset_mm)
    return Poligono(punti=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), stile="armatura")


def _barre_tese(inputs: TraveRettangolareInput) -> Barre:
    xs = _bar_positions_m(inputs.n_ferri1, inputs.b_mm, inputs.copriferro_mm)
    y = mm_to_m(inputs.copriferro_mm)
    return Barre(centri=tuple((x, y) for x in xs), diametro=mm_to_m(inputs.diametro_ferri1_mm), stile="armatura")


def _barre_compresse(inputs: TraveRettangolareInput) -> Barre | None:
    if inputs.n_ferri2 <= 0:
        return None
    xs = _bar_positions_m(inputs.n_ferri2, inputs.b_mm, inputs.copriferro_mm)
    y = mm_to_m(inputs.h_mm - inputs.copriferro_mm)
    return Barre(centri=tuple((x, y) for x in xs), diametro=mm_to_m(inputs.diametro_ferri2_mm), stile="armatura")


def _asse_neutro(inputs: TraveRettangolareInput, flessione: FlessioneOutput) -> Linea:
    """Profondità x dell'asse neutro, misurata dal lembo compresso (superiore)."""
    y_m = mm_to_m(inputs.h_mm - flessione.y_mm)
    return Linea(p1=(0.0, y_m), p2=(mm_to_m(inputs.b_mm), y_m), stile="evidenza", tratteggio=True)


def _quote(inputs: TraveRettangolareInput) -> tuple[Quota, Quota]:
    b_m, h_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm)
    scostamento = _MARGINE_QUOTA * max(b_m, h_m)
    quota_b = Quota(p1=(0.0, 0.0), p2=(b_m, 0.0), distanza=-scostamento, testo=etichetta_quota("b", inputs.b_mm, "mm", 0))
    quota_h = Quota(p1=(0.0, 0.0), p2=(0.0, h_m), distanza=scostamento, testo=etichetta_quota("h", inputs.h_mm, "mm", 0))
    return quota_b, quota_h


def _sezione(inputs: TraveRettangolareInput, flessione: FlessioneOutput) -> Vista:
    b_m, h_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm)
    quota_b, quota_h = _quote(inputs)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=b_m, h=h_m, stile="calcestruzzo"),
        _staffa(inputs),
        _barre_tese(inputs),
    ]
    compresse = _barre_compresse(inputs)
    if compresse is not None:
        forme.append(compresse)
    forme.append(_asse_neutro(inputs, flessione))
    forme.append(quota_b)
    forme.append(quota_h)
    return Vista(titolo="Sezione", forme=tuple(forme))

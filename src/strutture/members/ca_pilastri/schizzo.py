"""Live sketch for `pilastro-rettangolare`/`pilastro-circolare`: "Sezione" (concrete outline,
stirrup outline, perimeter longitudinal bars at true diameter, dimensions) —
docs/ui/WORKBENCH_SPEC.md §7. Pure functions of the validated inputs; a failure here must never
fail the calculation (guarded in `tool_rettangolare.py`/`tool_circolare.py`).

The rectangular bar layout uses `n_ferri_l1` (bars on the short L1-parallel faces, corners
included) purely for the drawing — the field's own description says so, it never enters any
verification."""
import math

from strutture.shared.sketch import Barre, Cerchio, Poligono, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import PilastroCircolareInput, PilastroRettangolareInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota


def disegna_rettangolare(inputs: PilastroRettangolareInput) -> Sketch:
    """Sezione l1×l2 del pilastro, con staffa e ferri longitudinali al perimetro."""
    return Sketch(viste=(_sezione_rettangolare(inputs),))


def disegna_circolare(inputs: PilastroCircolareInput) -> Sketch:
    """Sezione circolare del pilastro, con staffa e ferri longitudinali sulla circonferenza."""
    return Sketch(viste=(_sezione_circolare(inputs),))


def _linspace(a: float, b: float, n: int) -> tuple[float, ...]:
    if n <= 1:
        return ((a + b) / 2.0,)
    passo = (b - a) / (n - 1)
    return tuple(a + i * passo for i in range(n))


def _punti_perimetro_mm(l1_mm: float, l2_mm: float, c_mm: float, n_ferri: int, n_ferri_l1: int) -> tuple[tuple[float, float], ...]:
    """Posizioni delle barre longitudinali sul perimetro della gabbia (solo per il disegno)."""
    n_l2 = max(2, round((n_ferri - 2 * n_ferri_l1 + 4) / 2))
    xs = _linspace(c_mm, l1_mm - c_mm, n_ferri_l1)
    ys_lati = _linspace(c_mm, l2_mm - c_mm, n_l2)
    ys_interni = ys_lati[1:-1]
    punti = [(x, c_mm) for x in xs] + [(x, l2_mm - c_mm) for x in xs]
    punti += [(c_mm, y) for y in ys_interni] + [(l1_mm - c_mm, y) for y in ys_interni]
    return tuple(punti)


def _staffa_rettangolare(l1_mm: float, l2_mm: float, c_mm: float, diametro_staffe_mm: float) -> Poligono:
    inset_mm = c_mm - diametro_staffe_mm / 2.0
    x0, y0 = mm_to_m(inset_mm), mm_to_m(inset_mm)
    x1, y1 = mm_to_m(l1_mm - inset_mm), mm_to_m(l2_mm - inset_mm)
    return Poligono(punti=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), stile="armatura")


def _sezione_rettangolare(inputs: PilastroRettangolareInput) -> Vista:
    l1_m, l2_m = mm_to_m(inputs.l1_mm), mm_to_m(inputs.l2_mm)
    scostamento = _MARGINE_QUOTA * max(l1_m, l2_m)
    punti_mm = _punti_perimetro_mm(inputs.l1_mm, inputs.l2_mm, inputs.c_mm, inputs.n_ferri, inputs.n_ferri_l1)
    forme = (
        Rettangolo(x=0.0, y=0.0, w=l1_m, h=l2_m, stile="calcestruzzo"),
        _staffa_rettangolare(inputs.l1_mm, inputs.l2_mm, inputs.c_mm, inputs.diametro_staffe_mm),
        Barre(centri=tuple((mm_to_m(x), mm_to_m(y)) for x, y in punti_mm), diametro=mm_to_m(inputs.diametro_ferri_mm), stile="armatura"),
        Quota(p1=(0.0, 0.0), p2=(l1_m, 0.0), distanza=-scostamento, testo=etichetta_quota("L_1", inputs.l1_mm, "mm", 0)),
        Quota(p1=(0.0, 0.0), p2=(0.0, l2_m), distanza=scostamento, testo=etichetta_quota("L_2", inputs.l2_mm, "mm", 0)),
    )
    return Vista(titolo="Sezione", forme=forme)


def _punti_circonferenza_mm(d_mm: float, c_mm: float, n_ferri: int) -> tuple[tuple[float, float], ...]:
    raggio_ferri_mm = d_mm / 2.0 - c_mm
    return tuple(
        (raggio_ferri_mm * math.cos(2.0 * math.pi * i / n_ferri), raggio_ferri_mm * math.sin(2.0 * math.pi * i / n_ferri))
        for i in range(n_ferri)
    )


def _sezione_circolare(inputs: PilastroCircolareInput) -> Vista:
    r_m = mm_to_m(inputs.d_mm) / 2.0
    inset_mm = inputs.c_mm - inputs.diametro_staffe_mm / 2.0
    punti_mm = _punti_circonferenza_mm(inputs.d_mm, inputs.c_mm, inputs.n_ferri)
    scostamento = _MARGINE_QUOTA * 2.0 * r_m
    forme = (
        Cerchio(centro=(0.0, 0.0), r=r_m, stile="calcestruzzo"),
        Cerchio(centro=(0.0, 0.0), r=mm_to_m(inputs.d_mm / 2.0 - inset_mm), stile="armatura"),
        Barre(centri=tuple((mm_to_m(x), mm_to_m(y)) for x, y in punti_mm), diametro=mm_to_m(inputs.diametro_ferri_mm), stile="armatura"),
        Quota(p1=(-r_m, 0.0), p2=(r_m, 0.0), distanza=-(r_m + scostamento), testo=etichetta_quota("D", inputs.d_mm, "mm", 0)),
    )
    return Vista(titolo="Sezione", forme=forme)

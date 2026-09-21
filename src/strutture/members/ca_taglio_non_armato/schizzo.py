"""Live sketch for `ca-taglio-non-armato`: "Sezione" (concrete outline, tension-bar row at the
effective depth, b/d dimensions) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated
inputs + the geometry result; a failure here must never fail the calculation (guarded in
`compose.run`)."""
import math

from strutture.shared.sketch import Barre, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import GeometriaOutput, TaglioNonArmatoInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota

# Diametro solo per il disegno quando Asl e' nota come area diretta (nessun N°/Ø in input):
# non entra in nessun calcolo, serve solo a stimare quante barre "illustrative" disegnare.
DIAMETRO_ILLUSTRATIVO_MM = 16.0


_NOTA_DIAMETRO_ILLUSTRATIVO = (
    "Diametro delle barre illustrativo (Asl inserita direttamente, senza N° e Ø): non rappresenta "
    "un diametro commerciale reale e non è usato in alcun calcolo."
)


def disegna(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> Sketch:
    """Sezione b×d della sezione priva di armatura trasversale, con la riga di barre tese."""
    illustrativo = inputs.n_barre is None or inputs.diametro_barre_mm is None
    nota = _NOTA_DIAMETRO_ILLUSTRATIVO if illustrativo else ""
    return Sketch(viste=(_sezione(inputs, geometria),), nota=nota)


def _bar_positions_m(n: int, b_mm: float, copriferro_mm: float) -> tuple[float, ...]:
    """Ascisse delle barre di uno strato, distribuite tra i due copriferri laterali."""
    if n <= 1:
        return (mm_to_m(b_mm / 2.0),)
    passo_mm = (b_mm - 2.0 * copriferro_mm) / (n - 1)
    return tuple(mm_to_m(copriferro_mm + i * passo_mm) for i in range(n))


def _barre_tese(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> Barre:
    n, diametro_mm, illustrativo = _n_e_diametro(inputs, geometria)
    xs = _bar_positions_m(n, inputs.bw_mm, inputs.c_mm)
    y = mm_to_m(inputs.c_mm)
    stile = "fantasma" if illustrativo else "armatura"
    return Barre(centri=tuple((x, y) for x in xs), diametro=mm_to_m(diametro_mm), stile=stile)


def _n_e_diametro(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> tuple[int, float, bool]:
    """Barre da disegnare: diametro vero se N°/Ø sono stati dati in input, altrimenti un numero di
    barre stimato dal diametro illustrativo fisso a partire dall'area Asl risolta (terzo valore:
    True se il diametro è illustrativo, non un dato vero)."""
    if inputs.n_barre is not None and inputs.diametro_barre_mm is not None:
        return inputs.n_barre, inputs.diametro_barre_mm, False
    area_barra_mm2 = math.pi / 4.0 * DIAMETRO_ILLUSTRATIVO_MM**2
    n = max(1, round(geometria.asl_mm2 / area_barra_mm2))
    return n, DIAMETRO_ILLUSTRATIVO_MM, True


def _quote(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> tuple[Quota, Quota]:
    b_m, h_m = mm_to_m(inputs.bw_mm), mm_to_m(inputs.h_mm)
    c_m = mm_to_m(inputs.c_mm)
    scostamento = _MARGINE_QUOTA * max(b_m, h_m)
    quota_b = Quota(p1=(0.0, 0.0), p2=(b_m, 0.0), distanza=-scostamento,
                     testo=etichetta_quota("b", inputs.bw_mm, "mm", 0))
    # d misurato dal lembo compresso (sommita') fino alla riga di barre tese, non l'altezza h intera.
    # p1 -> p2 scende lungo il lato sinistro: la sinistra del segmento e' l'INTERNO della sezione, quindi distanza negativa.
    quota_d = Quota(p1=(0.0, h_m), p2=(0.0, c_m), distanza=-scostamento,
                     testo=etichetta_quota("d", geometria.d_mm, "mm", 0))
    return quota_b, quota_d


def _sezione(inputs: TaglioNonArmatoInput, geometria: GeometriaOutput) -> Vista:
    b_m, h_m = mm_to_m(inputs.bw_mm), mm_to_m(inputs.h_mm)
    quota_b, quota_d = _quote(inputs, geometria)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=b_m, h=h_m, stile="calcestruzzo"),
        _barre_tese(inputs, geometria),
        quota_b,
        quota_d,
    ]
    return Vista(titolo="Sezione", forme=tuple(forme))

"""Live sketch for `acciaio-colonna-h-ec3`: "Sezione" (H/I profile centred at the origin, y-y/z-z
axes, b/h/tw/tf dimensions) — docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in shared/sketch.py.
Pure function of the validated inputs; a failure here must never fail the calculation (guarded in
`tool.run`).

Real web/flange thicknesses are routinely < 2 % of the section's larger side (a real sliver at
drawing scale): both get a schematic minimum thickness (rule 2), while the quota TEXT always shows
the true tw/tf. The y-y/z-z axis end labels are kept off the centreline where the perpendicular
quota's own text sits (h/b are centred on y=0/x=0): y-y moves to the axis' LEFT end (opposite h,
clear of t_f which lives near the top); z-z stays at the top but is nudged sideways by a full `b_m`
to clear t_w's wide centred text box — verified empirically against several realistic H/I
proportions (`tests/.../test_schizzo.py`)."""
from strutture.shared.sketch import Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import ColonnaEc3Input

_MARGINE_ASSI = 1.15  # frazione della semidimensione, per l'estensione degli assi oltre il profilo
_SPESSORE_MINIMO_FRAZIONE = 0.03  # spessore minimo disegnato di ali/anima, frazione del lato maggiore (regola 2)
_NUDGE_Z_FRAZIONE_B = 1.0  # scostamento laterale dell'etichetta z, frazione di b_m, per liberare la quota t_w
# Quota(distanza): positivo = a sinistra del verso p1->p2 (ruotando p1->p2 di 90 gradi in senso antiorario).
_SCOSTAMENTO_H = -0.15  # quota h verticale lungo x=+b/2: negativo sposta a destra (fuori dal profilo)
_SCOSTAMENTO_TF = 0.15  # quota tf verticale lungo x=-b/2: positivo sposta a sinistra (lato opposto a h)
_SCOSTAMENTO_B = -0.15  # quota b orizzontale lungo y=-h/2: negativo sposta in basso (fuori dal profilo)
_SCOSTAMENTO_TW = 0.15  # quota tw orizzontale lungo y=+h/2: positivo sposta in alto (fuori dal profilo)


def disegna(inputs: ColonnaEc3Input) -> Sketch:
    """Sezione H/I della colonna, centrata nell'origine (x=0 in mezzeria anima, y=0 in mezzeria)."""
    return Sketch(viste=(_sezione(inputs),))


def _spessori_disegnati_m(b_m: float, h_m: float, tw_m: float, tf_m: float) -> tuple[float, float]:
    """(tw_disegnato, tf_disegnato): spessore reale, o il minimo schematico se è uno sliver."""
    maggiore_m = _MARGINE_ASSI * max(b_m, h_m)
    minimo_m = _SPESSORE_MINIMO_FRAZIONE * maggiore_m
    return max(tw_m, minimo_m), max(tf_m, minimo_m)


def _profilo(b_m: float, h_m: float, tw_dis_m: float, tf_dis_m: float) -> tuple[Rettangolo, Rettangolo, Rettangolo]:
    ala_superiore = Rettangolo(x=-b_m / 2, y=h_m / 2 - tf_dis_m, w=b_m, h=tf_dis_m, stile="acciaio")
    ala_inferiore = Rettangolo(x=-b_m / 2, y=-h_m / 2, w=b_m, h=tf_dis_m, stile="acciaio")
    anima = Rettangolo(x=-tw_dis_m / 2, y=-h_m / 2 + tf_dis_m, w=tw_dis_m, h=h_m - 2 * tf_dis_m, stile="acciaio")
    return ala_superiore, ala_inferiore, anima


def _assi(b_m: float, h_m: float) -> tuple[Linea, Etichetta, Linea, Etichetta]:
    """y-y all'estremo SINISTRO (libero da h, a destra, e da t_f, che sta in alto a sinistra);
    z-z in alto, spostata lateralmente di un intero `b_m` per non sovrapporsi al testo di t_w."""
    estremo_yy = (b_m / 2) * _MARGINE_ASSI
    asse_yy = Linea(p1=(-estremo_yy, 0.0), p2=(estremo_yy, 0.0), stile="asse")
    etichetta_yy = Etichetta(punto=(-estremo_yy, 0.0), simbolo="y", ancora="end", stile="asse")
    estremo_zz = (h_m / 2) * _MARGINE_ASSI
    asse_zz = Linea(p1=(0.0, -estremo_zz), p2=(0.0, estremo_zz), stile="asse")
    etichetta_zz = Etichetta(punto=(_NUDGE_Z_FRAZIONE_B * b_m, estremo_zz), simbolo="z", ancora="start", stile="asse")
    return asse_yy, etichetta_yy, asse_zz, etichetta_zz


def _quote(inputs: ColonnaEc3Input, b_m: float, h_m: float, tw_dis_m: float, tf_dis_m: float) -> tuple[Quota, Quota, Quota, Quota]:
    """h e tf sono verticali su lati opposti del profilo; b e tw sono orizzontali sopra/sotto.
    Le linee di quota di t_f/t_w seguono lo spessore DISEGNATO (per toccare la forma), il testo
    riporta sempre il valore VERO."""
    quota_h = Quota(
        p1=(b_m / 2, -h_m / 2), p2=(b_m / 2, h_m / 2), distanza=_SCOSTAMENTO_H * b_m,
        testo=etichetta_quota("h", inputs.h_mm, "mm", 0),
    )
    quota_tf = Quota(
        p1=(-b_m / 2, h_m / 2 - tf_dis_m), p2=(-b_m / 2, h_m / 2), distanza=_SCOSTAMENTO_TF * b_m,
        testo=etichetta_quota("t_f", inputs.tf_mm, "mm", 0),
    )
    quota_b = Quota(
        p1=(-b_m / 2, -h_m / 2), p2=(b_m / 2, -h_m / 2), distanza=_SCOSTAMENTO_B * h_m,
        testo=etichetta_quota("b", inputs.b_mm, "mm", 0),
    )
    quota_tw = Quota(
        p1=(-tw_dis_m / 2, h_m / 2), p2=(tw_dis_m / 2, h_m / 2), distanza=_SCOSTAMENTO_TW * h_m,
        testo=etichetta_quota("t_w", inputs.tw_mm, "mm", 0),
    )
    return quota_h, quota_tf, quota_b, quota_tw


def _sezione(inputs: ColonnaEc3Input) -> Vista:
    b_m, h_m, tw_m, tf_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm), mm_to_m(inputs.tw_mm), mm_to_m(inputs.tf_mm)
    tw_dis_m, tf_dis_m = _spessori_disegnati_m(b_m, h_m, tw_m, tf_m)
    ala_superiore, ala_inferiore, anima = _profilo(b_m, h_m, tw_dis_m, tf_dis_m)
    asse_yy, etichetta_yy, asse_zz, etichetta_zz = _assi(b_m, h_m)
    quota_h, quota_tf, quota_b, quota_tw = _quote(inputs, b_m, h_m, tw_dis_m, tf_dis_m)
    forme = (
        ala_superiore, ala_inferiore, anima,
        asse_yy, etichetta_yy, asse_zz, etichetta_zz,
        quota_h, quota_tf, quota_b, quota_tw,
    )
    return Vista(titolo="Sezione", forme=forme)

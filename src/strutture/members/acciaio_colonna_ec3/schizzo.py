"""Live sketch for `acciaio-colonna-h-ec3`: "Sezione" (H/I profile centred at the origin, y-y/z-z
axes, b/h/tw/tf dimensions) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs;
a failure here must never fail the calculation (guarded in `tool.run`)."""
from strutture.shared.sketch import Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .models import ColonnaEc3Input

_MARGINE_ASSI = 1.15  # frazione della semidimensione, per l'estensione degli assi oltre il profilo
# Quota(distanza): positivo = a sinistra del verso p1->p2 (ruotando p1->p2 di 90 gradi in senso antiorario).
_SCOSTAMENTO_H = -0.15  # quota h verticale lungo x=+b/2: negativo sposta a destra (fuori dal profilo)
_SCOSTAMENTO_TF = 0.15  # quota tf verticale lungo x=-b/2: positivo sposta a sinistra (lato opposto a h)
_SCOSTAMENTO_B = -0.15  # quota b orizzontale lungo y=-h/2: negativo sposta in basso (fuori dal profilo)
_SCOSTAMENTO_TW = 0.15  # quota tw orizzontale lungo y=+h/2: positivo sposta in alto (fuori dal profilo)


def disegna(inputs: ColonnaEc3Input) -> Sketch:
    """Sezione H/I della colonna, centrata nell'origine (x=0 in mezzeria anima, y=0 in mezzeria)."""
    return Sketch(viste=(_sezione(inputs),))


def _profilo(inputs: ColonnaEc3Input) -> tuple[Rettangolo, Rettangolo, Rettangolo]:
    b_m, h_m, tw_m, tf_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm), mm_to_m(inputs.tw_mm), mm_to_m(inputs.tf_mm)
    ala_superiore = Rettangolo(x=-b_m / 2, y=h_m / 2 - tf_m, w=b_m, h=tf_m, stile="acciaio")
    ala_inferiore = Rettangolo(x=-b_m / 2, y=-h_m / 2, w=b_m, h=tf_m, stile="acciaio")
    anima = Rettangolo(x=-tw_m / 2, y=-h_m / 2 + tf_m, w=tw_m, h=h_m - 2 * tf_m, stile="acciaio")
    return ala_superiore, ala_inferiore, anima


def _assi(inputs: ColonnaEc3Input) -> tuple[Linea, Etichetta, Linea, Etichetta]:
    b_m, h_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm)
    estremo_yy = (b_m / 2) * _MARGINE_ASSI
    asse_yy = Linea(p1=(-estremo_yy, 0.0), p2=(estremo_yy, 0.0), stile="asse")
    etichetta_yy = Etichetta(punto=(estremo_yy, 0.0), simbolo="y", ancora="start", stile="asse")
    estremo_zz = (h_m / 2) * _MARGINE_ASSI
    asse_zz = Linea(p1=(0.0, -estremo_zz), p2=(0.0, estremo_zz), stile="asse")
    etichetta_zz = Etichetta(punto=(0.0, estremo_zz), simbolo="z", ancora="start", stile="asse")
    return asse_yy, etichetta_yy, asse_zz, etichetta_zz


def _quote(inputs: ColonnaEc3Input) -> tuple[Quota, Quota, Quota, Quota]:
    """h e tf sono verticali su lati opposti del profilo; b e tw sono orizzontali sopra/sotto."""
    b_m, h_m, tw_m, tf_m = mm_to_m(inputs.b_mm), mm_to_m(inputs.h_mm), mm_to_m(inputs.tw_mm), mm_to_m(inputs.tf_mm)
    quota_h = Quota(
        p1=(b_m / 2, -h_m / 2), p2=(b_m / 2, h_m / 2), distanza=_SCOSTAMENTO_H * b_m,
        testo=etichetta_quota("h", inputs.h_mm, "mm", 0),
    )
    quota_tf = Quota(
        p1=(-b_m / 2, h_m / 2 - tf_m), p2=(-b_m / 2, h_m / 2), distanza=_SCOSTAMENTO_TF * b_m,
        testo=etichetta_quota("t_f", inputs.tf_mm, "mm", 0),
    )
    quota_b = Quota(
        p1=(-b_m / 2, -h_m / 2), p2=(b_m / 2, -h_m / 2), distanza=_SCOSTAMENTO_B * h_m,
        testo=etichetta_quota("b", inputs.b_mm, "mm", 0),
    )
    quota_tw = Quota(
        p1=(-tw_m / 2, h_m / 2), p2=(tw_m / 2, h_m / 2), distanza=_SCOSTAMENTO_TW * h_m,
        testo=etichetta_quota("t_w", inputs.tw_mm, "mm", 0),
    )
    return quota_h, quota_tf, quota_b, quota_tw


def _sezione(inputs: ColonnaEc3Input) -> Vista:
    ala_superiore, ala_inferiore, anima = _profilo(inputs)
    asse_yy, etichetta_yy, asse_zz, etichetta_zz = _assi(inputs)
    quota_h, quota_tf, quota_b, quota_tw = _quote(inputs)
    forme = (
        ala_superiore, ala_inferiore, anima,
        asse_yy, etichetta_yy, asse_zz, etichetta_zz,
        quota_h, quota_tf, quota_b, quota_tw,
    )
    return Vista(titolo="Sezione", forme=forme)

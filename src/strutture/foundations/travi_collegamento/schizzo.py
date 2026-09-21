"""Live sketch for `fond-trave-collegamento`: "Sezione" -- the tie-beam cross-section, the stirrup
outline inset by the cover, the longitudinal bars distributed around the inner perimeter, and
width/height dimensions -- docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs
(section + reinforcement are direct inputs for this sheet, not computed results); a failure here
must never fail the calculation (guarded in `tool_ntc.run_ntc` / `tool_en.run_en`).

Bar layout: walk the inner perimeter (inset `cf_mm + phi_staffa_mm + phi_mm/2` from each face --
the standard RC detailing centreline of the longitudinal bars) in `n_barre` equal arc-length steps
starting at the top-right corner. This naturally places a bar at/near every corner and spreads the
rest evenly along the sides; for `n_barre` < 4 the same walk simply distributes fewer points around
the same perimeter, without forcing all four corners."""
from strutture.shared.sketch import Barre, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .models import TraviCollegamentoInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_Lato = tuple[Punto, Punto, float]  # (estremo iniziale, estremo finale, lunghezza) di un lato


def disegna(inputs: TraviCollegamentoInput) -> Sketch:
    """Sezione trasversale della trave di collegamento con staffa e barre longitudinali."""
    return Sketch(viste=(_sezione(inputs),))


def _sezione(inputs: TraviCollegamentoInput) -> Vista:
    b, h = inputs.b_mm / 1000.0, inputs.h_mm / 1000.0
    scostamento = _MARGINE_QUOTA * max(b, h)
    forme = [
        Rettangolo(x=-b / 2, y=-h / 2, w=b, h=h, stile="calcestruzzo"),
        _staffa(inputs),
        _barre(inputs),
        Quota(p1=(-b / 2, -h / 2), p2=(b / 2, -h / 2), distanza=-scostamento, testo=etichetta_quota("B", b, "m")),
        Quota(p1=(-b / 2, -h / 2), p2=(-b / 2, h / 2), distanza=scostamento, testo=etichetta_quota("H", h, "m")),
    ]
    return Vista(titolo="Sezione", forme=tuple(forme))


def _staffa(inputs: TraviCollegamentoInput) -> Rettangolo:
    """Sagoma della staffa, scostata dai lembi della sezione del copriferro `cf_mm`."""
    b, h = inputs.b_mm / 1000.0, inputs.h_mm / 1000.0
    cf = inputs.cf_mm / 1000.0
    return Rettangolo(x=-b / 2 + cf, y=-h / 2 + cf, w=b - 2 * cf, h=h - 2 * cf, stile="armatura")


def _barre(inputs: TraviCollegamentoInput) -> Barre:
    """`n_barre` barre longitudinali sul perimetro interno (copriferro + staffa + mezzo diametro barra)."""
    b, h = inputs.b_mm / 1000.0, inputs.h_mm / 1000.0
    inset = (inputs.cf_mm + inputs.phi_staffa_mm + inputs.phi_mm / 2.0) / 1000.0
    centri = _punti_perimetro(b / 2 - inset, h / 2 - inset, inputs.n_barre)
    return Barre(centri=centri, diametro=inputs.phi_mm / 1000.0, stile="armatura")


def _punti_perimetro(half_b: float, half_h: float, n_punti: int) -> tuple[Punto, ...]:
    """`n_punti` punti a passo di uguale lunghezza d'arco lungo il perimetro del rettangolo di
    semilati `half_b`/`half_h`, a partire dallo spigolo in alto a destra."""
    lati: tuple[_Lato, ...] = (
        ((half_b, half_h), (-half_b, half_h), 2.0 * half_b),
        ((-half_b, half_h), (-half_b, -half_h), 2.0 * half_h),
        ((-half_b, -half_h), (half_b, -half_h), 2.0 * half_b),
        ((half_b, -half_h), (half_b, half_h), 2.0 * half_h),
    )
    perimetro = sum(lato[2] for lato in lati)
    passo = perimetro / n_punti
    return tuple(_punto_a_distanza(lati, (i * passo) % perimetro) for i in range(n_punti))


def _punto_a_distanza(lati: tuple[_Lato, ...], distanza: float) -> Punto:
    """Punto sul perimetro a `distanza` (lunghezza d'arco) dal primo estremo del primo lato."""
    percorsa = 0.0
    for (x0, y0), (x1, y1), lunghezza in lati:
        if lunghezza > 0.0 and distanza <= percorsa + lunghezza:
            frazione = (distanza - percorsa) / lunghezza
            return (x0 + frazione * (x1 - x0), y0 + frazione * (y1 - y0))
        percorsa += lunghezza
    return lati[-1][1]  # fallback per arrotondamenti in virgola mobile

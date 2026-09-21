"""Live sketch for `fond-plinto-isolato`: Pianta (footing, column, plan axes, eccentric resultant
of the governing row with its e_x/e_y) and Sezione (footing, column, load arrow N with M stated as
a label beside it, base-pressure diagram with sigma_max on the side of the eccentricity) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + the governing row; a failure
here must never fail the calculation (guarded in `tool.run`).

Both views are a SCHEMA (`Sketch.nota`): when there is no pedestal/bicchiere the column is still
drawn with an illustrative width/height so the view stays legible and within the 1:3.5-3.5:1
aspect target (`shared/sketch.py` COMPOSITION RULES) — its position/existence follows the inputs,
its size does not claim to be the real column size. A moment is not a force vector, so M is stated
in a label next to N rather than drawn as a straight arrow (that would misrepresent it)."""
from strutture.shared.sketch import (
    Cerchio,
    Diagramma,
    Etichetta,
    Freccia,
    Linea,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    etichetta_quota,
)

from .input import PlintoIsolatoInput
from .riga_verifica import RigaVerifica

_MARGINE_QUOTA = 0.07  # frazione del lato maggiore, per lo scostamento delle linee di quota (6-8 %)
_ASPETTO_BERSAGLIO = 3.0  # aspetto target della Sezione (< 3.5 di soglia, con margine)
_ALTEZZA_RELATIVA_DIAGRAMMA = 0.35
_STACCO_ETICHETTA_M = 0.03  # distanza orizzontale dell'etichetta M dal fusto di N, frazione di A_X
_ESTENSIONE_ASSI = 1.15  # gli assi sporgono oltre il plinto di questa frazione del semilato


def disegna(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Sketch:
    """Pianta + Sezione del plinto sotto la combinazione governante (pressione massima)."""
    return Sketch(
        viste=(_pianta(inputs, governante), _sezione(inputs, governante)),
        nota="Schema non in scala: il pilastro è indicativo quando assente il bicchiere",
    )


def _pianta(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, by = inputs.ax_m, inputs.by_m
    col_w, col_d = _colonna_pianta(inputs, ax, by)
    scostamento = _MARGINE_QUOTA * max(ax, by)
    forme = [
        Rettangolo(x=-ax / 2, y=-by / 2, w=ax, h=by, stile="calcestruzzo"),
        Rettangolo(x=-col_w / 2, y=-col_d / 2, w=col_w, h=col_d, stile="calcestruzzo"),
        Linea(p1=(-ax / 2 * _ESTENSIONE_ASSI, 0.0), p2=(ax / 2 * _ESTENSIONE_ASSI, 0.0), stile="asse"),
        Linea(p1=(0.0, -by / 2 * _ESTENSIONE_ASSI), p2=(0.0, by / 2 * _ESTENSIONE_ASSI), stile="asse"),
        *_eccentricita(governante, ax, by),
        Quota(p1=(-ax / 2, -by / 2), p2=(ax / 2, -by / 2), distanza=-scostamento,
              testo=etichetta_quota("A_X", ax, "m")),
        Quota(p1=(-ax / 2, -by / 2), p2=(-ax / 2, by / 2), distanza=scostamento,
              testo=etichetta_quota("B_Y", by, "m")),
    ]
    return Vista(titolo="Pianta", forme=tuple(forme))


def _eccentricita(governante: RigaVerifica, ax: float, by: float) -> tuple:
    """Punto della risultante eccentrica della combinazione governante, con le sue componenti
    e_x/e_y accanto (solo il valore in `testo`: il simbolo è già reso da `Etichetta.simbolo`)."""
    ex, ey = governante.ex_m, governante.ey_m
    raggio = 0.02 * max(ax, by)
    gap_x = 3.0 * raggio
    gap_y = 0.12 * max(ax, by)
    return (
        Cerchio(centro=(ex, ey), r=raggio, stile="evidenza"),
        Etichetta(punto=(ex + gap_x, ey + gap_y / 2), simbolo="e_x", testo=_valore_m(ex), ancora="start", stile="evidenza"),
        Etichetta(punto=(ex + gap_x, ey - gap_y / 2), simbolo="e_y", testo=_valore_m(ey), ancora="start", stile="evidenza"),
    )


def _valore_m(valore: float) -> str:
    return f"{valore:.2f} m".replace(".", ",")


def _colonna_pianta(inputs: PlintoIsolatoInput, ax: float, by: float) -> tuple[float, float]:
    """(larghezza, profondità) della colonna in pianta: dimensioni reali del bicchiere se presente,
    altrimenti un ingombro indicativo (stessa logica di `_colonna` per la Sezione)."""
    larghezza = inputs.a_pedestal_m if inputs.a_pedestal_m > 0 else min(max(0.25 * ax, 0.4), 0.5 * ax)
    profondita = inputs.b_pedestal_m if inputs.b_pedestal_m > 0 else min(max(0.25 * by, 0.4), 0.5 * by)
    return larghezza, profondita


def _colonna(inputs: PlintoIsolatoInput, ax: float, h: float) -> tuple[float, float]:
    """(larghezza, altezza) della colonna in sezione: dimensioni reali se c'è il bicchiere,
    altrimenti un ingombro indicativo dimensionato per tenere la Sezione entro l'aspetto target."""
    ha_bicchiere = inputs.a_pedestal_m > 0 and inputs.h_pedestal_sopra_m > 0
    larghezza = inputs.a_pedestal_m if inputs.a_pedestal_m > 0 else min(max(0.25 * ax, 0.4), 0.5 * ax)
    altezza_min_aspetto = max(ax / _ASPETTO_BERSAGLIO - h, 0.0)
    altezza = max(inputs.h_pedestal_sopra_m if ha_bicchiere else 0.0, altezza_min_aspetto, 0.4 * h)
    return larghezza, altezza


def _sezione(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, h = inputs.ax_m, inputs.h_plinto_m
    col_w, col_h = _colonna(inputs, ax, h)
    altezza_totale = h + col_h
    y_sommo = altezza_totale
    scostamento = _MARGINE_QUOTA * ax
    lunghezza_freccia_n = 0.5 * altezza_totale
    forme = [
        Rettangolo(x=-ax / 2, y=0.0, w=ax, h=h, stile="calcestruzzo"),
        Rettangolo(x=-col_w / 2, y=h, w=col_w, h=col_h, stile="calcestruzzo"),
        Freccia(coda=(0.0, y_sommo + lunghezza_freccia_n), punta=(0.0, y_sommo), stile="carico",
                 testo=etichetta_quota("N", governante.n_kN, "kN", 0)),
        # M a fianco del fusto di N (a metà altezza), non impilata sopra: il testo di N sta sopra
        # la coda, e una seconda riga più in alto sbilanciava la vista verso l'alto.
        Etichetta(punto=(_STACCO_ETICHETTA_M * ax, y_sommo + 0.5 * lunghezza_freccia_n), simbolo="M",
                   testo=_valore_kNm(governante.myy_kNm), ancora="start", stile="carico"),
        # A_X è già quotata in Pianta; sotto la base la quota finiva sulla riga delle etichette
        # σmin/σmax del diagramma. Qui si quota l'altezza H, a destra (V entra da sinistra):
        # verso l'alto la sinistra di p1->p2 è -x, quindi distanza negativa = fuori dal plinto.
        Quota(p1=(ax / 2, 0.0), p2=(ax / 2, h), distanza=-scostamento, testo=etichetta_quota("H", h, "m")),
        _diagramma_pressioni(governante, ax),
    ]
    if abs(governante.mu_scorrimento or 0.0) > 1e-9:
        lunghezza_freccia_v = max(0.3 * col_h, 0.3)
        forme.append(Freccia(coda=(-ax / 2 - lunghezza_freccia_v, h / 2), punta=(-ax / 2, h / 2),
                              stile="carico", testo="V"))
    return Vista(titolo="Sezione", forme=tuple(forme))


def _valore_kNm(valore: float) -> str:
    return f"{valore:.0f} kNm"


def _diagramma_pressioni(governante: RigaVerifica, ax: float) -> Diagramma:
    """`base` runs right (x=+ax/2) -> left (x=-ax/2); `valori` must put σmax on the side the
    resultant is eccentric towards (ex>=0 -> +x is more loaded -> σmax at base[0]=+ax/2; ex<0 ->
    σmax at base[1]=-ax/2), not always at the same end regardless of the actual eccentricity.
    Zero ends (fully out-of-kern crack) stay unlabelled."""
    if governante.ex_m >= 0:
        coppie = (("σmax", governante.sigma_max_kpa), ("σmin", governante.sigma_min_kpa))
    else:
        coppie = (("σmin", governante.sigma_min_kpa), ("σmax", governante.sigma_max_kpa))
    return Diagramma(
        base=((ax / 2, 0.0), (-ax / 2, 0.0)),  # right->left: ordinates hang below the footing base
        valori=tuple(v for _, v in coppie),
        etichette=tuple(_etichetta_pressione(s, v) for s, v in coppie),
        stile="pressione",
        altezza_relativa=_ALTEZZA_RELATIVA_DIAGRAMMA,
    )


def _etichetta_pressione(simbolo: str, valore_kpa: float) -> str:
    return etichetta_quota(simbolo, valore_kpa, "kPa", 0) if valore_kpa > 0 else ""

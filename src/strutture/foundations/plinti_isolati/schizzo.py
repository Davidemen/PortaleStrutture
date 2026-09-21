"""Live sketch for `fond-plinto-isolato`: Pianta (footing, pedestal, eccentric resultant,
dimensions) and Sezione (footing, column, load arrows N/M/V, base-pressure diagram with
sigma_max/sigma_min of the governing row) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the
validated inputs + the governing row; a failure here must never fail the calculation (guarded
in `tool.run`).

Sezione is a SCHEMA (`Sketch.nota`): when there is no pedestal/bicchiere the column is still drawn
with an illustrative width/height so the view stays legible and within the 1:3.5-3.5:1 aspect
target (`shared/sketch.py` COMPOSITION RULES) — its position/existence follows the inputs, its
size does not claim to be the real column size."""
from strutture.shared.sketch import (
    Cerchio,
    Diagramma,
    Etichetta,
    Freccia,
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


def disegna(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Sketch:
    """Pianta + Sezione del plinto sotto la combinazione governante (pressione massima)."""
    return Sketch(
        viste=(_pianta(inputs, governante), _sezione(inputs, governante)),
        nota="Schema non in scala: il pilastro è indicativo quando assente il bicchiere",
    )


def _pianta(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, by = inputs.ax_m, inputs.by_m
    scostamento = _MARGINE_QUOTA * max(ax, by)
    forme = [
        Rettangolo(x=-ax / 2, y=-by / 2, w=ax, h=by, stile="calcestruzzo"),
        *_pilastro_pianta(inputs),
        Cerchio(centro=(governante.ex_m, governante.ey_m), r=0.02 * max(ax, by), stile="carico"),
        Etichetta(punto=(governante.ex_m, governante.ey_m), simbolo="N", ancora="start", stile="carico"),
        Quota(p1=(-ax / 2, -by / 2), p2=(ax / 2, -by / 2), distanza=-scostamento,
              testo=etichetta_quota("A_X", ax, "m")),
        Quota(p1=(-ax / 2, -by / 2), p2=(-ax / 2, by / 2), distanza=scostamento,
              testo=etichetta_quota("B_Y", by, "m")),
    ]
    return Vista(titolo="Pianta", forme=tuple(forme))


def _pilastro_pianta(inputs: PlintoIsolatoInput) -> tuple[Rettangolo, ...]:
    if inputs.a_pedestal_m <= 0 or inputs.b_pedestal_m <= 0:
        return ()
    return (Rettangolo(x=-inputs.a_pedestal_m / 2, y=-inputs.b_pedestal_m / 2,
                        w=inputs.a_pedestal_m, h=inputs.b_pedestal_m, stile="calcestruzzo"),)


def _colonna(inputs: PlintoIsolatoInput, ax: float, h: float) -> tuple[float, float]:
    """(larghezza, altezza) della colonna: dimensioni reali se c'è il bicchiere, altrimenti un
    ingombro indicativo dimensionato per tenere la Sezione entro l'aspetto target."""
    ha_bicchiere = inputs.a_pedestal_m > 0 and inputs.h_pedestal_sopra_m > 0
    larghezza = inputs.a_pedestal_m if inputs.a_pedestal_m > 0 else min(max(0.25 * ax, 0.4), 0.5 * ax)
    altezza_min_aspetto = max(ax / _ASPETTO_BERSAGLIO - h, 0.0)
    altezza = max(inputs.h_pedestal_sopra_m if ha_bicchiere else 0.0, altezza_min_aspetto, 0.4 * h)
    return larghezza, altezza


def _sezione(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, h = inputs.ax_m, inputs.h_plinto_m
    col_w, col_h = _colonna(inputs, ax, h)
    y_sommo = h + col_h
    scostamento = _MARGINE_QUOTA * ax
    lunghezza_freccia = max(0.3 * col_h, 0.3)
    forme = [
        Rettangolo(x=-ax / 2, y=0.0, w=ax, h=h, stile="calcestruzzo"),
        Rettangolo(x=-col_w / 2, y=h, w=col_w, h=col_h, stile="calcestruzzo"),
        Freccia(coda=(0.0, y_sommo + lunghezza_freccia), punta=(0.0, y_sommo), stile="carico",
                 testo=etichetta_quota("N", governante.n_kN, "kN", 0)),
        Quota(p1=(-ax / 2, 0.0), p2=(ax / 2, 0.0), distanza=-scostamento,
              testo=etichetta_quota("A_X", ax, "m")),
        _diagramma_pressioni(governante, ax),
    ]
    if abs(governante.myy_kNm) > 1e-9:
        y_m = y_sommo + lunghezza_freccia + max(0.5 * col_h, 0.4)
        forme.append(Freccia(coda=(-0.3 * col_w, y_m), punta=(0.3 * col_w, y_m), stile="carico",
                              testo=etichetta_quota("M", governante.myy_kNm, "kNm", 0)))
    if abs(governante.mu_scorrimento or 0.0) > 1e-9:
        forme.append(Freccia(coda=(-ax / 2 - lunghezza_freccia, h / 2), punta=(-ax / 2, h / 2),
                              stile="carico", testo="V"))
    return Vista(titolo="Sezione", forme=tuple(forme))


def _diagramma_pressioni(governante: RigaVerifica, ax: float) -> Diagramma:
    return Diagramma(
        base=((ax / 2, 0.0), (-ax / 2, 0.0)),  # right->left: ordinates hang below the footing base
        valori=(governante.sigma_max_kpa, governante.sigma_min_kpa),
        etichette=(etichetta_quota("σmax", governante.sigma_max_kpa, "kPa", 0),
                   etichetta_quota("σmin", governante.sigma_min_kpa, "kPa", 0)),
        stile="pressione",
    )

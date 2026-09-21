"""Live sketch for `fond-plinto-isolato`: Pianta (footing, pedestal, eccentric resultant,
dimensions) and Sezione (footing, pedestal, load arrows N/M, base-pressure diagram with
sigma_max/sigma_min of the governing row) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the
validated inputs + the governing row; a failure here must never fail the calculation (guarded
in `tool.run`)."""
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

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_ALTEZZA_PILASTRO_MIN_M = 0.3  # altezza minima disegnata per il tratto di pilastro fuori terra


def disegna(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Sketch:
    """Pianta + Sezione del plinto sotto la combinazione governante (pressione massima)."""
    return Sketch(viste=(_pianta(inputs, governante), _sezione(inputs, governante)))


def _pianta(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, by = inputs.ax_m, inputs.by_m
    scostamento = _MARGINE_QUOTA * max(ax, by)
    forme = [
        Rettangolo(x=-ax / 2, y=-by / 2, w=ax, h=by, stile="calcestruzzo"),
        *_pilastro_pianta(inputs),
        Cerchio(centro=(governante.ex_m, governante.ey_m), r=0.02 * max(ax, by), stile="carico"),
        Etichetta(punto=(governante.ex_m, governante.ey_m), testo="", simbolo="N",
                   ancora="start", stile="carico"),
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


def _sezione(inputs: PlintoIsolatoInput, governante: RigaVerifica) -> Vista:
    ax, h = inputs.ax_m, inputs.h_plinto_m
    pilastro, y_carico, y_sommo = _pilastro_sezione(inputs, h)
    forme = [
        Rettangolo(x=-ax / 2, y=0.0, w=ax, h=h, stile="calcestruzzo"),
        *pilastro,
        Freccia(coda=(0.0, y_carico + 0.6), punta=(0.0, y_carico), stile="carico",
                 testo=etichetta_quota("N", governante.n_kN, "kN", 0)),
        Quota(p1=(-ax / 2, y_sommo), p2=(ax / 2, y_sommo), distanza=_MARGINE_QUOTA * ax,
              testo=etichetta_quota("A_X", ax, "m")),
        _diagramma_pressioni(governante, ax),
    ]
    if abs(governante.myy_kNm) > 1e-9:
        forme.append(Freccia(coda=(-0.3, y_carico + 0.4), punta=(0.3, y_carico + 0.4), stile="carico",
                              testo=etichetta_quota("M", governante.myy_kNm, "kNm", 0)))
    if abs(governante.mu_scorrimento or 0.0) > 1e-9:
        forme.append(Freccia(coda=(-ax / 2 - 0.5, 0.02), punta=(-ax / 2, 0.02), stile="carico", testo="V"))
    return Vista(titolo="Sezione", forme=tuple(forme))


def _pilastro_sezione(inputs: PlintoIsolatoInput, h: float) -> tuple[tuple[Rettangolo, ...], float, float]:
    """Returns (shapes, y del punto di applicazione del carico, y sommitale disegnata)."""
    if inputs.a_pedestal_m <= 0:
        return (), h, h
    h_pilastro = max(inputs.h_pedestal_sopra_m, _ALTEZZA_PILASTRO_MIN_M)
    rettangolo = Rettangolo(x=-inputs.a_pedestal_m / 2, y=h, w=inputs.a_pedestal_m, h=h_pilastro,
                             stile="calcestruzzo")
    sommo = h + h_pilastro
    return (rettangolo,), sommo, sommo


def _diagramma_pressioni(governante: RigaVerifica, ax: float) -> Diagramma:
    return Diagramma(
        base=((ax / 2, 0.0), (-ax / 2, 0.0)),  # right->left: ordinates hang below the footing base
        valori=(governante.sigma_max_kpa, governante.sigma_min_kpa),
        etichette=(etichetta_quota("σmax", governante.sigma_max_kpa, "kPa", 0),
                   etichetta_quota("σmin", governante.sigma_min_kpa, "kPa", 0)),
        stile="pressione",
    )

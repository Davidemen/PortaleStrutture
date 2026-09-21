"""Live sketch for `fond-plinto-su-pali`: Pianta (cap, column, piles at true diameter, spacings)
and Prospetto S&T (struts, ties, governing pile reaction) — docs/ui/WORKBENCH_SPEC.md §7. Pure
function of the validated inputs + computed results; a failure here must never fail the
calculation (guarded in `tool.run`)."""
from strutture.shared.pile_group import PilePos
from strutture.shared.sketch import Barre, Freccia, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .input import PlintoSuPaliInput
from .models_puntoni_tiranti import PuntoniTiranti

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_ARMA_FRECCIA_M = 0.5  # lunghezza della freccia di reazione, sopra la testa palo


def disegna(inputs: PlintoSuPaliInput, piles: tuple[PilePos, ...], puntoni_tiranti: PuntoniTiranti,
            n_max_pila_kN: float) -> Sketch:
    """Pianta del plinto su pali + prospetto del meccanismo puntoni-tiranti governante."""
    return Sketch(viste=(_pianta(inputs, piles), _prospetto(inputs, puntoni_tiranti, n_max_pila_kN)))


def _pianta(inputs: PlintoSuPaliInput, piles: tuple[PilePos, ...]) -> Vista:
    ax, by = inputs.ax_m, inputs.by_m
    scostamento = _MARGINE_QUOTA * max(ax, by)
    forme = [
        Rettangolo(x=-ax / 2, y=-by / 2, w=ax, h=by, stile="calcestruzzo"),
        Rettangolo(x=-inputs.bx_pilastro_m / 2, y=-inputs.by_pilastro_m / 2,
                   w=inputs.bx_pilastro_m, h=inputs.by_pilastro_m, stile="calcestruzzo"),
        Barre(centri=tuple((p.x_m, p.y_m) for p in piles), diametro=inputs.diametro_pila_mm / 1000.0, stile="palo"),
        Quota(p1=(-ax / 2, -by / 2), p2=(ax / 2, -by / 2), distanza=-scostamento,
              testo=etichetta_quota("A_X", ax, "m")),
        Quota(p1=(-ax / 2, -by / 2), p2=(-ax / 2, by / 2), distanza=scostamento,
              testo=etichetta_quota("B_Y", by, "m")),
    ]
    forme.extend(_quote_interassi(inputs, piles))
    return Vista(titolo="Pianta", forme=tuple(forme))


def _quote_interassi(inputs: PlintoSuPaliInput, piles: tuple[PilePos, ...]) -> tuple[Quota, ...]:
    """Interasse pali lungo X (se >1 colonna) e lungo Y (se >1 riga), sotto/sopra i pali stessi."""
    xs = sorted({p.x_m for p in piles})
    ys = sorted({p.y_m for p in piles})
    quote: list[Quota] = []
    if len(xs) > 1:
        quote.append(Quota(p1=(xs[0], ys[0]), p2=(xs[-1], ys[0]), distanza=-_MARGINE_QUOTA * inputs.by_m * 0.6,
                            testo=etichetta_quota("L_X", inputs.lx_m, "m")))
    if len(ys) > 1:
        quote.append(Quota(p1=(xs[0], ys[0]), p2=(xs[0], ys[-1]), distanza=_MARGINE_QUOTA * inputs.ax_m * 0.6,
                            testo=etichetta_quota("L_Y", inputs.ly_m, "m")))
    return tuple(quote)


def _prospetto(inputs: PlintoSuPaliInput, puntoni_tiranti: PuntoniTiranti, n_max_pila_kN: float) -> Vista:
    """Prospetto simmetrico del meccanismo governante: un palo per lato a distanza `lxy_m` dal
    baricentro (per lo schema 2x2 rappresenta la sezione diagonale, identica su ogni puntone per
    simmetria); appoggio diretto (schema 1x1, `theta_deg is None`) disegna solo colonna e palo."""
    h = inputs.h_plinto_m
    puntone = puntoni_tiranti.puntone
    forme: list = [Rettangolo(x=-inputs.ax_m / 2, y=0.0, w=inputs.ax_m, h=h, stile="calcestruzzo")]
    if puntone.theta_deg is None or puntone.lxy_m <= 0:
        forme.append(Barre(centri=((0.0, 0.0),), diametro=inputs.diametro_pila_mm / 1000.0, stile="palo"))
        forme.append(Freccia(coda=(0.0, -_ARMA_FRECCIA_M), punta=(0.0, 0.0), stile="reazione",
                              testo=etichetta_quota("N", n_max_pila_kN, "kN", 0)))
        return Vista(titolo="Prospetto S&T", forme=tuple(forme))
    lxy, nodo_y = puntone.lxy_m, puntone.h_wt2_m
    forme.append(Barre(centri=((-lxy, 0.0), (lxy, 0.0)), diametro=inputs.diametro_pila_mm / 1000.0, stile="palo"))
    for segno in (-1.0, 1.0):
        forme.append(Linea(p1=(segno * lxy, 0.0), p2=(0.0, nodo_y), stile="puntone"))
        forme.append(Freccia(coda=(segno * lxy, -_ARMA_FRECCIA_M), punta=(segno * lxy, 0.0), stile="reazione",
                              testo=etichetta_quota("N", n_max_pila_kN, "kN", 0)))
    if _ha_tirante(puntoni_tiranti):
        forme.append(Linea(p1=(-lxy, nodo_y), p2=(lxy, nodo_y), stile="tirante"))
    return Vista(titolo="Prospetto S&T", forme=tuple(forme))


def _ha_tirante(puntoni_tiranti: PuntoniTiranti) -> bool:
    return any(t is not None for t in (puntoni_tiranti.tirante_xy, puntoni_tiranti.tirante_x, puntoni_tiranti.tirante_y))

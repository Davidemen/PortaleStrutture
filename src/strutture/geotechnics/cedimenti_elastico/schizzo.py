"""Live sketches for `geo-cedimento-elastico-newmark` and `geo-cedimento-elastico-timoshenko-
goodier` (docs/ui/WORKBENCH_SPEC.md §7): a "Sezione" view (footing, embedment, soil layers with
their modulus labels, integration-depth line) for both tools, plus a "Pianta" view (comparison
rectangle, O and O') for Newmark in modalità PUNTO. Pure functions of the validated inputs; a
failure here must never fail the calculation (guarded in each tool's `run_*`).

Neither tool has an oedometric "Z,crit" concept; both integrate to a fixed depth instead
(Newmark's `z_max`, measured below the foundation base; Timoshenko-Goodier's significant depth
`H`, also below the base) — drawn as the requested `stile="evidenza"` line, playing the same role.

Coordinates: y=0 at ground level, y UP -> depths below ground are negative y (`shared/sketch.py`).
`strati[i].z_top_m`/`z_bot_m` are ground-relative here (`docs/specs/geo-cedimenti-elastico.md`
rows 58/69: "depth-from-ground top/bottom") — drawn directly, never shifted (`ground_to_base.
shift_to_base` is an internal step of the physics only). `z_max`/`h_significativo`, instead, are
measured below the foundation base, so they ARE offset by `d_m` here."""
from strutture.shared.sketch import Cerchio, Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.soil_layers import SoilLayer

from .boundary import SistemaUnita, to_m
from .models_newmark import NewmarkInput
from .models_tg import TimoshenkoGoodierInput

_SPESSORE_PLINTO_NOMINALE_M = 0.3  # spessore illustrativo del plinto: non è un dato di ingresso
_MARGINE_QUOTA = 0.15  # frazione della dimensione maggiore, per lo scostamento delle quote
_MARGINE_ETICHETTA_M = 0.4
_FATTORE_LARGHEZZA_TERRENO = 1.6  # gli strati sono disegnati più larghi del plinto, solo per leggibilità
H_SIGNIFICATIVO_DEFAULT_FACTOR = 5.0  # rispecchia il default di tool_timoshenko_goodier.py


def disegna_newmark(inputs: NewmarkInput) -> Sketch:
    """Sezione (+ Pianta con O/O' in modalità PUNTO) del cedimento elastico di Newmark."""
    sistema = inputs.sistema_unita
    d_m = to_m(inputs.d, sistema)
    z_max_m = to_m(inputs.z_max, sistema)
    larghezza_plinto = _larghezza_plinto_newmark(inputs, sistema)
    sezione = _sezione(d_m, larghezza_plinto, inputs.strati, d_m + z_max_m, "z_max")
    if inputs.modalita != "PUNTO":
        return Sketch(viste=(sezione,))
    return Sketch(viste=(sezione, _pianta_punto(inputs, sistema)))


def disegna_timoshenko_goodier(inputs: TimoshenkoGoodierInput) -> Sketch:
    """Sezione del cedimento elastico di Timoshenko & Goodier, con la profondità significativa H."""
    sistema = inputs.sistema_unita
    d_m = to_m(inputs.d, sistema)
    b_m = to_m(inputs.b, sistema)
    h_m = to_m(inputs.h_significativo, sistema) if inputs.h_significativo is not None else H_SIGNIFICATIVO_DEFAULT_FACTOR * b_m
    return Sketch(viste=(_sezione(d_m, b_m, inputs.strati, d_m + h_m, "H"),))


def _larghezza_plinto_newmark(inputs: NewmarkInput, sistema: SistemaUnita) -> float:
    if inputs.modalita == "CENTRO":
        assert inputs.b is not None  # garantito da `_valida_modalita`
        return to_m(inputs.b, sistema)
    assert inputs.side_p is not None  # garantito da `_valida_modalita`
    return to_m(inputs.side_p, sistema)


def _sezione(d_m: float, larghezza_plinto: float, strati: tuple[SoilLayer, ...],
             profondita_evidenza_m: float, etichetta_evidenza: str) -> Vista:
    larghezza_terreno = larghezza_plinto * _FATTORE_LARGHEZZA_TERRENO
    forme = [
        Rettangolo(x=-larghezza_plinto / 2, y=-d_m, w=larghezza_plinto, h=_SPESSORE_PLINTO_NOMINALE_M, stile="calcestruzzo"),
        *_strati_forme(strati, larghezza_terreno),
        *_evidenza(profondita_evidenza_m, larghezza_terreno, etichetta_evidenza),
        Quota(p1=(-larghezza_plinto / 2, 0.0), p2=(larghezza_plinto / 2, 0.0),
              distanza=_MARGINE_QUOTA * larghezza_plinto, testo=etichetta_quota("B", larghezza_plinto, "m")),
    ]
    if d_m > 0:
        x_d = larghezza_plinto / 2 + _MARGINE_QUOTA * larghezza_plinto
        forme.append(Quota(p1=(x_d, 0.0), p2=(x_d, -d_m), distanza=_MARGINE_QUOTA * larghezza_plinto,
                            testo=etichetta_quota("D", d_m, "m")))
    return Vista(titolo="Sezione", forme=tuple(forme))


def _strati_forme(strati: tuple[SoilLayer, ...], larghezza_terreno: float) -> tuple[Rettangolo | Etichetta, ...]:
    forme: list[Rettangolo | Etichetta] = []
    for strato in strati:
        y_top, y_bot = -strato.z_top_m, -strato.z_bot_m
        forme.append(Rettangolo(x=-larghezza_terreno / 2, y=y_bot, w=larghezza_terreno, h=y_top - y_bot, stile="terreno"))
        forme.append(Etichetta(punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, (y_top + y_bot) / 2),
                                testo=etichetta_quota("E", strato.modulo_MPa, "MPa", 1)))
    return tuple(forme)


def _evidenza(profondita_m: float, larghezza_terreno: float, etichetta: str) -> tuple[Linea, Etichetta]:
    y = -profondita_m
    linea = Linea(p1=(-larghezza_terreno / 2, y), p2=(larghezza_terreno / 2, y), stile="evidenza")
    testo = Etichetta(punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, y),
                       testo=etichetta_quota(etichetta, profondita_m, "m", 2), stile="evidenza")
    return linea, testo


def _pianta_punto(inputs: NewmarkInput, sistema: SistemaUnita) -> Vista:
    """O' = (0,0); il lato O'd corre lungo x (lunghezza `side_p`), il lato O'g lungo y (lunghezza
    `side_q`); O = (e1, e2) — e1 = distanza di O dal lato O'g misurata lungo O'd, e2 = distanza di
    O dal lato O'd misurata lungo O'g (può cadere fuori dal rettangolo: geometria valida per il
    metodo di Newmark per sovrapposizione)."""
    assert inputs.side_p is not None and inputs.side_q is not None  # garantito da `_valida_modalita`
    assert inputs.e1 is not None and inputs.e2 is not None
    side_p_m, side_q_m = to_m(inputs.side_p, sistema), to_m(inputs.side_q, sistema)
    e1_m, e2_m = to_m(inputs.e1, sistema), to_m(inputs.e2, sistema)
    raggio = 0.02 * max(side_p_m, side_q_m)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=side_p_m, h=side_q_m, stile="calcestruzzo"),
        Cerchio(centro=(0.0, 0.0), r=raggio, stile="asse"),
        Etichetta(punto=(0.0, 0.0), testo="O'", ancora="end", stile="asse"),
        Cerchio(centro=(e1_m, e2_m), r=raggio, stile="carico"),
        Etichetta(punto=(e1_m, e2_m), testo="O", ancora="start", stile="carico"),
        Quota(p1=(0.0, 0.0), p2=(side_p_m, 0.0), distanza=-_MARGINE_QUOTA * side_q_m,
              testo=etichetta_quota("O'd", side_p_m, "m")),
        Quota(p1=(0.0, 0.0), p2=(0.0, side_q_m), distanza=-_MARGINE_QUOTA * side_p_m,
              testo=etichetta_quota("O'g", side_q_m, "m")),
    ]
    return Vista(titolo="Pianta", forme=tuple(forme))

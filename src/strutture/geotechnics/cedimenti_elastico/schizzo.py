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
measured below the foundation base, so they are converted to an absolute (ground-relative) depth
by the caller before reaching `_sezione`.

The real stratigraphy/integration depth can span tens of metres under a footing a few metres wide
(COMPOSITION RULES in `shared/sketch.py`: schema, not scale). Depth is capped to keep the view
within the aspect target; layers/lines beyond the cap are dropped and a short dashed `fantasma`
mark shows the section continues, while every text still reports the true value. At most
`_MAX_STRATI_ETICHETTATI` layers are labelled (evenly spread by depth, not by table row) so texts
never crowd each other regardless of how many rows the `strati` table has."""
from strutture.shared.sketch import Cerchio, Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.soil_layers import SoilLayer

from .boundary import SistemaUnita, to_m
from .models_newmark import NewmarkInput
from .models_tg import TimoshenkoGoodierInput

_SPESSORE_PLINTO_NOMINALE_M = 0.3  # spessore illustrativo del plinto: non è un dato di ingresso
_SPESSORE_PLINTO_FRAZIONE = 0.03  # spessore minimo schematico, come frazione dell'altezza della vista
_MARGINE_QUOTA = 0.07  # frazione della dimensione maggiore, per lo scostamento delle quote (6-8 %)
_MARGINE_ETICHETTA_M = 0.4
_FATTORE_LARGHEZZA_TERRENO = 3.0  # il blocco di terreno è disegnato 3 volte più largo del plinto
_LUNGHEZZA_FANTASMA_LATERALE_M = 0.3  # tacco fantasma ai lati del blocco di terreno
_ASPETTO_BUDGET_PROFONDITA = 2.2  # profondità visibile massima, come multiplo della larghezza (< 3.5 di soglia)
_FRAZIONE_FANTASMA = 0.08  # lunghezza del tratto "continua oltre", come frazione della profondità visibile
_MAX_STRATI_ETICHETTATI = 2  # strati con quota di spessore + etichetta E, indipendentemente dalla tabella
H_SIGNIFICATIVO_DEFAULT_FACTOR = 5.0  # rispecchia il default di tool_timoshenko_goodier.py


def disegna_newmark(inputs: NewmarkInput) -> Sketch:
    """Sezione (+ Pianta con O/O' in modalità PUNTO) del cedimento elastico di Newmark."""
    sistema = inputs.sistema_unita
    d_m = to_m(inputs.d, sistema)
    z_max_m = to_m(inputs.z_max, sistema)
    larghezza_plinto = _larghezza_plinto_newmark(inputs, sistema)
    sezione, ritagliato = _sezione(d_m, larghezza_plinto, inputs.strati, d_m + z_max_m, "z_max")
    if inputs.modalita != "PUNTO":
        return Sketch(viste=(sezione,), nota=_nota(ritagliato, d_m))
    return Sketch(viste=(sezione, _pianta_punto(inputs, sistema)), nota=_nota(ritagliato, d_m))


def disegna_timoshenko_goodier(inputs: TimoshenkoGoodierInput) -> Sketch:
    """Sezione del cedimento elastico di Timoshenko & Goodier, con la profondità significativa H."""
    sistema = inputs.sistema_unita
    d_m = to_m(inputs.d, sistema)
    b_m = to_m(inputs.b, sistema)
    h_m = to_m(inputs.h_significativo, sistema) if inputs.h_significativo is not None else H_SIGNIFICATIVO_DEFAULT_FACTOR * b_m
    sezione, ritagliato = _sezione(d_m, b_m, inputs.strati, d_m + h_m, "H")
    return Sketch(viste=(sezione,), nota=_nota(ritagliato, d_m))


def _nota(ritagliato: bool, d_m: float) -> str:
    """D (piano di posa) sta nella nota e non in una quota: i due fianchi del blocco di terreno sono
    già occupati (spessori di strato a sinistra, moduli a destra) e una quota di D o si sovrapponeva
    a quei testi o finiva staccata dal disegno, lontano a destra."""
    parti = ["Schema non in scala"]
    if d_m > 0:
        parti.append(f"piano di posa a D = {d_m:.2f} m dal piano campagna".replace(".", ","))
    if ritagliato:
        parti.append("stratigrafia interrotta oltre la quota indicata")
    return ", ".join(parti)


def _larghezza_plinto_newmark(inputs: NewmarkInput, sistema: SistemaUnita) -> float:
    if inputs.modalita == "CENTRO":
        assert inputs.b is not None  # garantito da `_valida_modalita`
        return to_m(inputs.b, sistema)
    assert inputs.side_p is not None  # garantito da `_valida_modalita`
    return to_m(inputs.side_p, sistema)


def _sezione(d_m: float, larghezza_plinto: float, strati: tuple[SoilLayer, ...],
             profondita_evidenza_m: float, etichetta_evidenza: str) -> tuple[Vista, bool]:
    larghezza_terreno = larghezza_plinto * _FATTORE_LARGHEZZA_TERRENO
    profondita_reale = max(max((s.z_bot_m for s in strati), default=0.0), profondita_evidenza_m)
    profondita_visibile = min(profondita_reale, larghezza_terreno * _ASPETTO_BUDGET_PROFONDITA)
    ritagliato = profondita_reale > profondita_visibile + 1e-9
    spessore_plinto = max(_SPESSORE_PLINTO_NOMINALE_M, _SPESSORE_PLINTO_FRAZIONE * profondita_visibile)

    # scostamento sul lato maggiore della vista (non solo la larghezza del plinto): con una
    # stratigrafia profonda la vista e' molto piu' alta che larga, e le quote devono restare
    # separate anche quando il testo occupa piu' spazio "modello" alla scala ridotta.
    margine = _MARGINE_QUOTA * max(larghezza_terreno, profondita_visibile)
    profondita_evidenza_disegnata = min(profondita_evidenza_m, profondita_visibile)
    y_sommo_plinto = -d_m + spessore_plinto
    forme = [
        Rettangolo(x=-larghezza_plinto / 2, y=-d_m, w=larghezza_plinto, h=spessore_plinto, stile="calcestruzzo"),
        *_strati_forme(strati, larghezza_terreno, profondita_visibile, profondita_evidenza_disegnata),
        *_evidenza(profondita_evidenza_disegnata, profondita_evidenza_m, larghezza_terreno, etichetta_evidenza),
        *_fantasma_laterale(larghezza_terreno, profondita_visibile),
        # B sopra il plinto (non sotto): resta cosi' sempre distinta dalle quote di spessore strato,
        # che stanno sotto e a sinistra.
        Quota(p1=(-larghezza_plinto / 2, y_sommo_plinto), p2=(larghezza_plinto / 2, y_sommo_plinto),
              distanza=margine, testo=etichetta_quota("B", larghezza_plinto, "m")),
    ]
    if ritagliato:
        forme.append(_fantasma_profondita(profondita_visibile))
    return Vista(titolo="Sezione", forme=tuple(forme)), ritagliato


def _fantasma_laterale(larghezza_terreno: float, profondita_visibile: float) -> tuple[Linea, Linea]:
    """Tacchi tratteggiati ai due lati del blocco di terreno, a mezza altezza: il blocco è
    volutamente disegnato 3 volte più largo del plinto (non si legga come un palo), e questi segnano
    che il terreno prosegue lateralmente oltre il bordo disegnato."""
    y = -profondita_visibile / 2.0
    meta = larghezza_terreno / 2.0
    return (
        Linea(p1=(-meta, y), p2=(-meta - _LUNGHEZZA_FANTASMA_LATERALE_M, y), stile="fantasma", tratteggio=True),
        Linea(p1=(meta, y), p2=(meta + _LUNGHEZZA_FANTASMA_LATERALE_M, y), stile="fantasma", tratteggio=True),
    )


def _strati_visibili(strati: tuple[SoilLayer, ...], profondita_visibile: float) -> list[tuple[SoilLayer, float, float]]:
    visibili = []
    for strato in strati:
        if strato.z_top_m >= profondita_visibile:
            continue
        visibili.append((strato, -strato.z_top_m, -min(strato.z_bot_m, profondita_visibile)))
    return visibili


_MIN_SCOSTAMENTO_ETICHETTA_FRAZIONE = 0.12  # distanza minima fra due etichette, come frazione della vista


def _indici_da_etichettare(visibili: list[tuple[SoilLayer, float, float]], profondita_visibile: float,
                            y_evidenza: float) -> set[int]:
    """Al massimo `_MAX_STRATI_ETICHETTATI` indici, scelti per profondità reale target equispaziata
    su tutta l'altezza visibile (non per indice di strato), cosi' le etichette non si affollano mai;
    uno strato la cui etichetta cadrebbe troppo vicino alla linea di evidenza (`y_evidenza`) resta
    senza testo (la linea/il suo valore restano comunque leggibili da soli)."""
    n = len(visibili)
    minimo = _MIN_SCOSTAMENTO_ETICHETTA_FRAZIONE * profondita_visibile
    candidati = range(n) if n <= _MAX_STRATI_ETICHETTATI else None
    if candidati is None:
        scelti: set[int] = set()
        for k in range(_MAX_STRATI_ETICHETTATI):
            target_y = -profondita_visibile * (k + 0.5) / _MAX_STRATI_ETICHETTATI
            indice = min(range(n), key=lambda i: abs((visibili[i][1] + visibili[i][2]) / 2 - target_y))
            scelti.add(indice)
        candidati = scelti
    return {i for i in candidati if abs((visibili[i][1] + visibili[i][2]) / 2 - y_evidenza) >= minimo}


def _strati_forme(strati: tuple[SoilLayer, ...], larghezza_terreno: float, profondita_visibile: float,
                   profondita_evidenza_disegnata: float) -> tuple[Rettangolo | Etichetta | Quota, ...]:
    """Ogni strato è un rettangolo; per gli strati scelti da `_indici_da_etichettare` compaiono
    anche la quota di spessore (a sinistra) e l'etichetta del modulo E (a destra) — mai sullo
    stesso lato, cosi' non si toccano mai."""
    visibili = _strati_visibili(strati, profondita_visibile)
    da_etichettare = _indici_da_etichettare(visibili, profondita_visibile, -profondita_evidenza_disegnata)
    margine_sinistra = _MARGINE_QUOTA * larghezza_terreno
    forme: list[Rettangolo | Etichetta | Quota] = []
    for indice, (strato, y_top, y_bot) in enumerate(visibili):
        forme.append(Rettangolo(x=-larghezza_terreno / 2, y=y_bot, w=larghezza_terreno,
                                 h=y_top - y_bot, stile="terreno"))
        if indice not in da_etichettare:
            continue
        forme.append(Etichetta(punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, (y_top + y_bot) / 2),
                                testo=etichetta_quota("E", strato.modulo_MPa, "MPa", 1)))
        forme.append(Quota(
            p1=(-larghezza_terreno / 2, y_top), p2=(-larghezza_terreno / 2, y_bot), distanza=-margine_sinistra,
            testo=etichetta_quota("Δz", y_top - y_bot, "m"),
        ))
    return tuple(forme)


def _evidenza(profondita_disegnata_m: float, profondita_reale_m: float, larghezza_terreno: float,
              etichetta: str) -> tuple[Linea, Etichetta]:
    """La linea è disegnata alla profondità reale, oppure al limite del ritaglio quando quella
    reale cade oltre (schema non in scala): l'etichetta riporta sempre il valore vero."""
    y = -profondita_disegnata_m
    linea = Linea(p1=(-larghezza_terreno / 2, y), p2=(larghezza_terreno / 2, y), stile="evidenza")
    testo = Etichetta(punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, y),
                       testo=etichetta_quota(etichetta, profondita_reale_m, "m", 2), stile="evidenza")
    return linea, testo


def _fantasma_profondita(profondita_visibile: float) -> Linea:
    """Tratteggio corto che segnala la prosecuzione della stratigrafia oltre il ritaglio in profondità."""
    y0 = -profondita_visibile
    y1 = y0 - _FRAZIONE_FANTASMA * profondita_visibile
    return Linea(p1=(0.0, y0), p2=(0.0, y1), stile="fantasma", tratteggio=True)


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
        Quota(p1=(0.0, 0.0), p2=(0.0, side_q_m), distanza=_MARGINE_QUOTA * side_p_m,
              testo=etichetta_quota("O'g", side_q_m, "m")),
    ]
    return Vista(titolo="Pianta", forme=tuple(forme))

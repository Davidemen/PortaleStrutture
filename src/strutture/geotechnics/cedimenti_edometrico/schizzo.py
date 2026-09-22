"""Live sketch for `geo-cedimento-edometrico`: one "Sezione" view (footing, soil layers with
per-layer thickness/modulus, water table, dashed 2:1 load-spread down to Z,crit, main dimensions)
— docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs and the already-computed
SI/critical-depth results; a failure here must never fail the calculation (guarded in `tool.run`).

Coordinates: y=0 at ground level, y UP -> depths below ground are negative y (`shared/sketch.py`).
`strati[i].z_top_m`/`z_bot_m` and `profondita_critica.z_crit_utilizzato_m` are BOTH measured below
the foundation base (piano di posa), NOT from ground, for THIS package specifically — this is the
opposite convention from `cedimenti_elastico` (whose `strati` genuinely are ground-relative, see
that package's own `schizzo.py`). Verified directly against the code: `righe.py`'s `genera_righe`
passes `inputs.strati` UNMODIFIED into `eed_kpa(layers, z_m)`, where `z_m` (`RigaResult.z_m`) is
"Profondità dal piano di posa della fondazione" — for that lookup to be physically meaningful,
`strati` must already share that same base-relative origin (confirmed by
`docs/specs/geo-cedimenti-edometrico.md` rows 50-57). Both are offset by `si.d_m` here.

The real stratigraphy/critical-depth can span tens of metres under a footing a few metres wide
(COMPOSITION RULES in `shared/sketch.py`: schema, not scale). Depth is capped to keep the view
within the aspect target; layers/lines beyond the cap are dropped and a short dashed `fantasma`
mark shows the section continues (both in depth, and sideways: the soil block is drawn 3x the
footing width, wider than a footing could ever read as, with `fantasma` ticks at its sides), while
every text still reports the true value. At most `_MAX_STRATI_ETICHETTATI` layers get a thickness
quota (left) + a modulus label (right) so texts never crowd each other regardless of how many rows
the `strati` table has."""
from strutture.shared.sketch import Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.soil_layers import SoilLayer

from .ingresso import IngressoSI
from .models import EdometricoInput
from .profondita_critica import ProfonditaCriticaResult

_SPESSORE_PLINTO_NOMINALE_M = 0.3  # spessore illustrativo del plinto: non è un dato di ingresso
_SPESSORE_PLINTO_FRAZIONE = 0.03  # spessore minimo schematico, come frazione dell'altezza della vista
_MARGINE_QUOTA = 0.07  # frazione della larghezza del plinto, per lo scostamento delle quote (6-8 %)
_MARGINE_ETICHETTA_M = 0.4  # distanza delle etichette Eed/Z_crit oltre il bordo degli strati
_FATTORE_LARGHEZZA_TERRENO = 3.0  # il blocco di terreno è disegnato 3 volte più largo del plinto
_LUNGHEZZA_FANTASMA_LATERALE_M = 0.3  # tacco fantasma ai lati del blocco di terreno
_ASPETTO_BUDGET_PROFONDITA = 2.2  # profondità visibile massima, come multiplo della larghezza (< 3.5 di soglia)
_FRAZIONE_FANTASMA = 0.08  # lunghezza del tratto "continua oltre", come frazione della profondità visibile
_MAX_STRATI_ETICHETTATI = 2  # strati con quota di spessore + etichetta Eed, indipendentemente dalla tabella


def disegna(inputs: EdometricoInput, si: IngressoSI, profondita: ProfonditaCriticaResult) -> Sketch:
    """Sezione con plinto, stratigrafia (eventualmente ritagliata in profondità), falda (se
    presente e visibile), diffusione 2:1 tratteggiata fino a Z,crit e profondità critica Z,crit."""
    larghezza_terreno = si.b_m * _FATTORE_LARGHEZZA_TERRENO
    profondita_reale = si.d_m + max(
        max((s.z_bot_m for s in inputs.strati), default=0.0), profondita.z_crit_utilizzato_m,
    )
    profondita_visibile = min(profondita_reale, larghezza_terreno * _ASPETTO_BUDGET_PROFONDITA)
    ritagliato = profondita_reale > profondita_visibile + 1e-9
    spessore_plinto = max(_SPESSORE_PLINTO_NOMINALE_M, _SPESSORE_PLINTO_FRAZIONE * profondita_visibile)
    profondita_zcrit_disegnata = min(si.d_m + profondita.z_crit_utilizzato_m, profondita_visibile)

    forme = [
        _plinto(si, spessore_plinto),
        *_strati(inputs, si, larghezza_terreno, profondita_visibile),
        *_falda(si, larghezza_terreno, profondita_visibile),
        *_diffusione_2a1(si, profondita_zcrit_disegnata),
        *_zcrit(si, profondita, larghezza_terreno, profondita_visibile),
        *_fantasma_laterale(larghezza_terreno, profondita_visibile),
        *_quote(si, spessore_plinto, larghezza_terreno, profondita_visibile),
    ]
    if ritagliato:
        forme.append(_fantasma_profondita(profondita_visibile))
    nota = (
        "Schema non in scala"
        + _nota_piano_di_posa(si.d_m)
        + (", stratigrafia interrotta oltre la quota indicata" if ritagliato else "")
    )
    return Sketch(viste=(Vista(titolo="Sezione", forme=tuple(forme)),), nota=nota)


def _plinto(si: IngressoSI, spessore: float) -> Rettangolo:
    return Rettangolo(x=-si.b_m / 2, y=-si.d_m, w=si.b_m, h=spessore, stile="calcestruzzo")


def _diffusione_2a1(si: IngressoSI, profondita_zcrit_disegnata: float) -> tuple[Linea, Linea]:
    """Diffusione del carico 2:1 (metodo classico di stima di Δσ), tratteggiata, dal filo del plinto
    fino alla quota disegnata di Z,crit: per ogni unità di profondità la semi-diffusione cresce di
    metà unità in orizzontale."""
    profondita_diffusione = max(profondita_zcrit_disegnata - si.d_m, 0.0)
    sporgenza = profondita_diffusione / 2.0
    y0, y1 = -si.d_m, -profondita_zcrit_disegnata
    return (
        Linea(p1=(-si.b_m / 2, y0), p2=(-si.b_m / 2 - sporgenza, y1), stile="fantasma", tratteggio=True),
        Linea(p1=(si.b_m / 2, y0), p2=(si.b_m / 2 + sporgenza, y1), stile="fantasma", tratteggio=True),
    )


def _strati_visibili(inputs: EdometricoInput, si: IngressoSI,
                      profondita_visibile: float) -> list[tuple[SoilLayer, float, float]]:
    """(strato, y_top, y_bot) per ogni strato che ricade (anche parzialmente) entro la profondità
    visibile, con la base ritagliata alla quota di taglio quando necessario."""
    visibili = []
    for strato in inputs.strati:
        abs_top, abs_bot = si.d_m + strato.z_top_m, si.d_m + strato.z_bot_m
        if abs_top >= profondita_visibile:
            continue
        abs_bot = min(abs_bot, profondita_visibile)
        visibili.append((strato, -abs_top, -abs_bot))
    return visibili


def _indici_da_etichettare(visibili: list[tuple[SoilLayer, float, float]], profondita_visibile: float) -> set[int]:
    """Al massimo `_MAX_STRATI_ETICHETTATI` indici: il primo strato (più superficiale, il più
    rilevante per il cedimento immediato) è sempre incluso; gli altri sono scelti per profondità
    reale target equispaziata sull'altezza visibile (non per indice di strato), cosi' le etichette
    restano ben distanziate qualunque sia la stratigrafia."""
    n = len(visibili)
    if n <= _MAX_STRATI_ETICHETTATI:
        return set(range(n))
    scelti: set[int] = {0}
    rimanenti = _MAX_STRATI_ETICHETTATI - 1
    for k in range(rimanenti):
        target_y = -profondita_visibile * (k + 1) / (rimanenti + 1)
        indice_piu_vicino = min(
            (i for i in range(n) if i not in scelti),
            key=lambda i: abs((visibili[i][1] + visibili[i][2]) / 2 - target_y),
        )
        scelti.add(indice_piu_vicino)
    return scelti


def _strati(inputs: EdometricoInput, si: IngressoSI, larghezza_terreno: float,
            profondita_visibile: float) -> tuple[Rettangolo | Etichetta | Quota, ...]:
    """Ogni strato è un rettangolo; per gli strati scelti da `_indici_da_etichettare` compaiono
    anche la quota di spessore (a sinistra) e l'etichetta del modulo Eed (a destra) — mai sullo
    stesso lato, cosi' non si toccano mai."""
    visibili = _strati_visibili(inputs, si, profondita_visibile)
    da_etichettare = _indici_da_etichettare(visibili, profondita_visibile)
    margine_sinistra = _MARGINE_QUOTA * larghezza_terreno
    forme: list[Rettangolo | Etichetta | Quota] = []
    for indice, (strato, y_top, y_bot) in enumerate(visibili):
        forme.append(Rettangolo(x=-larghezza_terreno / 2, y=y_bot, w=larghezza_terreno,
                                 h=y_top - y_bot, stile="terreno"))
        if indice not in da_etichettare:
            continue
        forme.append(Etichetta(
            punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, (y_top + y_bot) / 2),
            testo=etichetta_quota("Eed", strato.modulo_MPa, "MPa", 1),
        ))
        forme.append(Quota(
            p1=(-larghezza_terreno / 2, y_top), p2=(-larghezza_terreno / 2, y_bot), distanza=-margine_sinistra,
            testo=etichetta_quota("Δz", y_top - y_bot, "m"), campo="dz",
        ))
    return tuple(forme)


def _falda(si: IngressoSI, larghezza_terreno: float, profondita_visibile: float) -> tuple[Linea, ...]:
    if si.falda_m is None or si.falda_m > profondita_visibile:
        return ()
    y = -si.falda_m
    return (Linea(p1=(-larghezza_terreno / 2, y), p2=(larghezza_terreno / 2, y), stile="acqua", tratteggio=True),)


def _zcrit(si: IngressoSI, profondita: ProfonditaCriticaResult, larghezza_terreno: float,
           profondita_visibile: float) -> tuple[Linea, Etichetta]:
    """La linea è disegnata alla profondità reale, oppure al limite del ritaglio quando quella
    reale cade oltre (schema non in scala): l'etichetta riporta sempre il valore vero."""
    profondita_assoluta_m = si.d_m + profondita.z_crit_utilizzato_m
    y = -min(profondita_assoluta_m, profondita_visibile)
    linea = Linea(p1=(-larghezza_terreno / 2, y), p2=(larghezza_terreno / 2, y), stile="evidenza")
    etichetta = Etichetta(
        punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, y),
        testo=etichetta_quota("Z_crit", profondita_assoluta_m, "m", 2), stile="evidenza",
    )
    return linea, etichetta


def _fantasma_profondita(profondita_visibile: float) -> Linea:
    """Tratteggio corto che segnala la prosecuzione della stratigrafia oltre il ritaglio in profondità."""
    y0 = -profondita_visibile
    y1 = y0 - _FRAZIONE_FANTASMA * profondita_visibile
    return Linea(p1=(0.0, y0), p2=(0.0, y1), stile="fantasma", tratteggio=True)


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


def _quote(si: IngressoSI, spessore_plinto: float, larghezza_terreno: float, profondita_visibile: float) -> tuple[Quota, ...]:
    """La quota B corre sopra il plinto (non sotto): resta cosi' sempre distinta dal diagramma /
    dalle quote di spessore strato, che stanno sotto e a sinistra. Lo scostamento è proporzionato
    al lato maggiore dell'INTERA vista (non solo a B): con una stratigrafia profonda la vista è
    molto più alta che larga e un testo, alla scala ridotta, occupa più spazio "modello".
    D (piano di posa) non è una quota ma sta nella nota (`_nota_piano_di_posa`): i due fianchi del
    blocco di terreno sono già occupati (spessori a sinistra, moduli a destra) e una quota di D o
    si sovrapponeva a quei testi o finiva staccata dal disegno, lontano a destra."""
    margine = _MARGINE_QUOTA * max(larghezza_terreno, profondita_visibile)
    y_sommo_plinto = -si.d_m + spessore_plinto
    return (
        Quota(
            p1=(-si.b_m / 2, y_sommo_plinto), p2=(si.b_m / 2, y_sommo_plinto), distanza=margine,
            testo=etichetta_quota("B", si.b_m, "m"), campo="b",
        ),
    )


def _nota_piano_di_posa(d_m: float) -> str:
    return f", piano di posa a D = {d_m:.2f} m dal piano campagna".replace(".", ",") if d_m > 0 else ""

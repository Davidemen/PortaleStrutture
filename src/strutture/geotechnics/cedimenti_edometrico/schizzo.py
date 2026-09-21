"""Live sketch for `geo-cedimento-edometrico`: one "Sezione" view (footing, soil layers, water
table, Z,crit line, main dimensions) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the
validated inputs and the already-computed SI/critical-depth results; a failure here must never
fail the calculation (guarded in `tool.run`).

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
mark shows the section continues, while every text still reports the true value. At most
`_MAX_STRATI_ETICHETTATI` layers are labelled (evenly spread across the visible ones) so texts
never crowd each other regardless of how many rows the `strati` table has."""
from strutture.shared.sketch import Etichetta, Linea, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.soil_layers import SoilLayer

from .ingresso import IngressoSI
from .models import EdometricoInput
from .profondita_critica import ProfonditaCriticaResult

_SPESSORE_PLINTO_NOMINALE_M = 0.3  # spessore illustrativo del plinto: non è un dato di ingresso
_SPESSORE_PLINTO_FRAZIONE = 0.03  # spessore minimo schematico, come frazione dell'altezza della vista
_MARGINE_QUOTA = 0.07  # frazione della larghezza del plinto, per lo scostamento delle quote (6-8 %)
_MARGINE_ETICHETTA_M = 0.4  # distanza delle etichette Eed/Z_crit oltre il bordo degli strati
_FATTORE_LARGHEZZA_TERRENO = 1.6  # gli strati/le linee sono disegnati più larghi del plinto, solo per leggibilità
_ASPETTO_BUDGET_PROFONDITA = 2.2  # profondità visibile massima, come multiplo della larghezza (< 3.5 di soglia)
_FRAZIONE_FANTASMA = 0.08  # lunghezza del tratto "continua oltre", come frazione della profondità visibile
_MAX_STRATI_ETICHETTATI = 3  # testi Eed al massimo, indipendentemente dal numero di strati in tabella


def disegna(inputs: EdometricoInput, si: IngressoSI, profondita: ProfonditaCriticaResult) -> Sketch:
    """Sezione con plinto, stratigrafia (eventualmente ritagliata in profondità), falda (se
    presente e visibile) e profondità critica Z,crit."""
    larghezza_terreno = si.b_m * _FATTORE_LARGHEZZA_TERRENO
    profondita_reale = si.d_m + max(
        max((s.z_bot_m for s in inputs.strati), default=0.0), profondita.z_crit_utilizzato_m,
    )
    profondita_visibile = min(profondita_reale, larghezza_terreno * _ASPETTO_BUDGET_PROFONDITA)
    ritagliato = profondita_reale > profondita_visibile + 1e-9
    spessore_plinto = max(_SPESSORE_PLINTO_NOMINALE_M, _SPESSORE_PLINTO_FRAZIONE * profondita_visibile)

    forme = [
        _plinto(si, spessore_plinto),
        *_strati(inputs, si, larghezza_terreno, profondita_visibile),
        *_falda(si, larghezza_terreno, profondita_visibile),
        *_zcrit(si, profondita, larghezza_terreno, profondita_visibile),
        *_quote(si),
    ]
    if ritagliato:
        forme.append(_fantasma(profondita_visibile))
    nota = "Schema non in scala" + (", stratigrafia interrotta oltre la quota indicata" if ritagliato else "")
    return Sketch(viste=(Vista(titolo="Sezione", forme=tuple(forme)),), nota=nota)


def _plinto(si: IngressoSI, spessore: float) -> Rettangolo:
    return Rettangolo(x=-si.b_m / 2, y=-si.d_m, w=si.b_m, h=spessore, stile="calcestruzzo")


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
    """Al massimo `_MAX_STRATI_ETICHETTATI` indici, scelti per profondità reale target equispaziata
    su tutta l'altezza visibile (non per indice di strato): uno strato sottile in mezzo a strati
    spessi non fa raggruppare le etichette, restano ben distanziate qualunque sia la stratigrafia."""
    n = len(visibili)
    if n <= _MAX_STRATI_ETICHETTATI:
        return set(range(n))
    scelti: set[int] = set()
    for k in range(_MAX_STRATI_ETICHETTATI):
        target_y = -profondita_visibile * (k + 0.5) / _MAX_STRATI_ETICHETTATI
        indice_piu_vicino = min(range(n), key=lambda i: abs((visibili[i][1] + visibili[i][2]) / 2 - target_y))
        scelti.add(indice_piu_vicino)
    return scelti


def _strati(inputs: EdometricoInput, si: IngressoSI, larghezza_terreno: float,
            profondita_visibile: float) -> tuple[Rettangolo | Etichetta, ...]:
    visibili = _strati_visibili(inputs, si, profondita_visibile)
    da_etichettare = _indici_da_etichettare(visibili, profondita_visibile)
    forme: list[Rettangolo | Etichetta] = []
    for indice, (strato, y_top, y_bot) in enumerate(visibili):
        forme.append(Rettangolo(x=-larghezza_terreno / 2, y=y_bot, w=larghezza_terreno,
                                 h=y_top - y_bot, stile="terreno"))
        if indice in da_etichettare:
            forme.append(Etichetta(
                punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, (y_top + y_bot) / 2),
                testo=etichetta_quota("Eed", strato.modulo_MPa, "MPa", 1),
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


def _fantasma(profondita_visibile: float) -> Linea:
    """Tratteggio corto che segnala la prosecuzione della stratigrafia oltre il ritaglio."""
    y0 = -profondita_visibile
    y1 = y0 - _FRAZIONE_FANTASMA * profondita_visibile
    return Linea(p1=(0.0, y0), p2=(0.0, y1), stile="fantasma", tratteggio=True)


def _quote(si: IngressoSI) -> tuple[Quota, ...]:
    """La quota B corre lungo la base del plinto (non lungo il piano campagna): la base è sempre il
    lato più basso del solido, quindi uno scostamento negativo (verso il basso) è sempre "fuori",
    a prescindere da quanto il plinto sporga sopra il piano campagna quando D è piccolo/nullo."""
    margine = _MARGINE_QUOTA * si.b_m
    quota_b = Quota(
        p1=(-si.b_m / 2, -si.d_m), p2=(si.b_m / 2, -si.d_m), distanza=-margine,
        testo=etichetta_quota("B", si.b_m, "m"),
    )
    if si.d_m <= 0:
        return (quota_b,)
    x_d = si.b_m / 2 + margine
    quota_d = Quota(p1=(x_d, 0.0), p2=(x_d, -si.d_m), distanza=margine, testo=etichetta_quota("D", si.d_m, "m"))
    return quota_b, quota_d

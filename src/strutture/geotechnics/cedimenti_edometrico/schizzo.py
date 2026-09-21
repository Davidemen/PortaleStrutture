"""Live sketch for `geo-cedimento-edometrico`: one "Sezione" view (footing, soil layers, water
table, Z,crit line, main dimensions) — docs/ui/WORKBENCH_SPEC.md §7. Pure function of the
validated inputs and the already-computed SI/critical-depth results; a failure here must never
fail the calculation (guarded in `tool.run`).

Coordinates: y=0 at ground level, y UP -> depths below ground are negative y (`shared/sketch.py`).
`strati[i].z_top_m`/`z_bot_m` and `profondita_critica.z_crit_utilizzato_m` are BOTH measured below
the foundation base (piano di posa), NOT from ground, for THIS package specifically — this is the
opposite convention from `cedimenti_elastico` (whose `strati` genuinely are ground-relative, see
that package's own `schizzo.py`). Verified directly against the code, not just the generic
architecture-doc line: `righe.py`'s `genera_righe` passes `inputs.strati` UNMODIFIED (no
`shift_to_base`-style conversion exists anywhere in this package) into `eed_kpa(layers, z_m)`,
where `z_m` is `RigaResult.z_m`, documented as "Profondità dal piano di posa della fondazione" —
for that lookup to be physically meaningful, `strati` must already share that same base-relative
origin. `docs/specs/geo-cedimenti-edometrico.md` rows 50-57 confirm both the layer table and the
depth table are "depth below foundation base". Both are offset by `si.d_m` here to place them at
their true absolute depth from ground — do not remove this offset."""
from strutture.shared.sketch import (
    Etichetta,
    Linea,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    etichetta_quota,
)

from .ingresso import IngressoSI
from .models import EdometricoInput
from .profondita_critica import ProfonditaCriticaResult

_SPESSORE_PLINTO_NOMINALE_M = 0.3  # spessore illustrativo del plinto: non è un dato di ingresso
_MARGINE_QUOTA = 0.15  # frazione della larghezza del plinto, per lo scostamento delle quote
_MARGINE_ETICHETTA_M = 0.4  # distanza delle etichette Eed/Z_crit oltre il bordo degli strati
_FATTORE_LARGHEZZA_TERRENO = 1.6  # gli strati/le linee sono disegnati più larghi del plinto, solo per leggibilità


def disegna(inputs: EdometricoInput, si: IngressoSI, profondita: ProfonditaCriticaResult) -> Sketch:
    """Sezione con plinto, stratigrafia, falda (se presente) e profondità critica Z,crit."""
    larghezza_terreno = si.b_m * _FATTORE_LARGHEZZA_TERRENO
    forme = [
        _plinto(si),
        *_strati(inputs, si, larghezza_terreno),
        *_falda(si, larghezza_terreno),
        *_zcrit(si, profondita, larghezza_terreno),
        *_quote(si),
    ]
    return Sketch(viste=(Vista(titolo="Sezione", forme=tuple(forme)),))


def _plinto(si: IngressoSI) -> Rettangolo:
    return Rettangolo(x=-si.b_m / 2, y=-si.d_m, w=si.b_m, h=_SPESSORE_PLINTO_NOMINALE_M, stile="calcestruzzo")


def _strati(inputs: EdometricoInput, si: IngressoSI, larghezza_terreno: float) -> tuple[Rettangolo | Etichetta, ...]:
    forme: list[Rettangolo | Etichetta] = []
    for strato in inputs.strati:
        y_top = -si.d_m - strato.z_top_m
        y_bot = -si.d_m - strato.z_bot_m
        forme.append(Rettangolo(
            x=-larghezza_terreno / 2, y=y_bot, w=larghezza_terreno, h=y_top - y_bot, stile="terreno",
        ))
        forme.append(Etichetta(
            punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, (y_top + y_bot) / 2),
            testo=etichetta_quota("Eed", strato.modulo_MPa, "MPa", 1),
        ))
    return tuple(forme)


def _falda(si: IngressoSI, larghezza_terreno: float) -> tuple[Linea, ...]:
    if si.falda_m is None:
        return ()
    return (Linea(
        p1=(-larghezza_terreno / 2, -si.falda_m), p2=(larghezza_terreno / 2, -si.falda_m),
        stile="acqua", tratteggio=True,
    ),)


def _zcrit(si: IngressoSI, profondita: ProfonditaCriticaResult, larghezza_terreno: float) -> tuple[Linea, Etichetta]:
    profondita_assoluta_m = si.d_m + profondita.z_crit_utilizzato_m
    y = -profondita_assoluta_m
    linea = Linea(p1=(-larghezza_terreno / 2, y), p2=(larghezza_terreno / 2, y), stile="evidenza")
    etichetta = Etichetta(
        punto=(larghezza_terreno / 2 + _MARGINE_ETICHETTA_M, y),
        testo=etichetta_quota("Z_crit", profondita_assoluta_m, "m", 2), stile="evidenza",
    )
    return linea, etichetta


def _quote(si: IngressoSI) -> tuple[Quota, ...]:
    margine = _MARGINE_QUOTA * si.b_m
    quota_b = Quota(
        p1=(-si.b_m / 2, 0.0), p2=(si.b_m / 2, 0.0), distanza=margine, testo=etichetta_quota("B", si.b_m, "m"),
    )
    if si.d_m <= 0:
        return (quota_b,)
    x_d = si.b_m / 2 + margine
    quota_d = Quota(p1=(x_d, 0.0), p2=(x_d, -si.d_m), distanza=margine, testo=etichetta_quota("D", si.d_m, "m"))
    return quota_b, quota_d

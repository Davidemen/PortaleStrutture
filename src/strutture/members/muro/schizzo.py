"""Live sketch for `muro-sostegno`: Sezione (stem, heel, toe, backfill, surcharge, static/seismic
thrust arrows at their heights, base-pressure diagram, main dimensions) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + computed results; a failure
here must never fail the calculation (guarded in `tool.run_muro_sostegno`).

Coordinates: x=0 at the toe/valle outer edge (the overturning pole), y=0 at the footing base —
the same reference `geometria_muro` already uses for every centroid."""
from strutture.shared.sketch import (
    Diagramma,
    Freccia,
    Poligono,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    etichetta_quota,
)

from .models import (
    GeometriaResult,
    MuroSostegnoInput,
    PressioniCombo,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)

_MARGINE_QUOTA = 0.15  # frazione della dimensione maggiore, per lo scostamento delle linee di quota
_SBALZO_SOVRACCARICO_M = 0.4  # lunghezza delle frecce di sovraccarico


def disegna(
    inputs: MuroSostegnoInput, geometria: GeometriaResult, spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...],
) -> Sketch:
    """Sezione trasversale del muro con spinte e diagramma delle pressioni di base."""
    return Sketch(viste=(_sezione(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno),))


def _faccia_interna_stem_x(y_m: float, inputs: MuroSostegnoInput) -> float:
    """Ascissa della faccia interna (lato monte/terreno) del paramento all'altezza `y_m`, che si
    rastrema linearmente da `s_base_m` (in fondazione) a `s_top_m` (in sommità)."""
    frac = max(0.0, min(1.0, (y_m - inputs.s_fond_m) / inputs.h_muro_m))
    return inputs.b_valle_m + inputs.s_base_m - frac * (inputs.s_base_m - inputs.s_top_m)


def _stem(inputs: MuroSostegnoInput) -> Poligono:
    y0, y1 = inputs.s_fond_m, inputs.s_fond_m + inputs.h_muro_m
    x_valle = inputs.b_valle_m + inputs.s_base_m  # faccia esterna (lato valle), verticale
    return Poligono(
        punti=(
            (inputs.b_valle_m, y0), (x_valle, y0), (x_valle, y1), (_faccia_interna_stem_x(y1, inputs), y1),
        ),
        stile="calcestruzzo",
    )


def _terreno(inputs: MuroSostegnoInput, geometria: GeometriaResult) -> Poligono:
    y0, y1 = inputs.s_fond_m, inputs.s_fond_m + inputs.h_muro_m
    x_stem_alto = _faccia_interna_stem_x(y1, inputs)
    x_stem_basso = inputs.b_valle_m + inputs.s_base_m
    return Poligono(
        punti=((x_stem_basso, y0), (geometria.b_fond_m, y0), (geometria.b_fond_m, y1), (x_stem_alto, y1)),
        stile="terreno",
    )


def _sovraccarico(inputs: MuroSostegnoInput, geometria: GeometriaResult) -> tuple[Freccia, ...]:
    """Frecce verticali del sovraccarico q sopra il cuneo di terreno (assenti se q=0)."""
    if inputs.q_kN_m2 <= 0:
        return ()
    y_top = inputs.s_fond_m + inputs.h_muro_m
    x_centro = (_faccia_interna_stem_x(y_top, inputs) + geometria.b_fond_m) / 2
    return (Freccia(coda=(x_centro, y_top + _SBALZO_SOVRACCARICO_M), punta=(x_centro, y_top), stile="carico",
                     testo=etichetta_quota("q", inputs.q_kN_m2, "kN/m2", 0)),)


def _spinta(nome_cercato: str, spinte: tuple[SpintaCombo, ...],
            ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...]) -> RibaltamentoScorrimentoCombo | None:
    for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True):
        if spinta.nome == nome_cercato:
            return verifica
    return None


def _freccia_spinta(verifica: RibaltamentoScorrimentoCombo, inputs: MuroSostegnoInput,
                     geometria: GeometriaResult, *, etichetta: str) -> Freccia:
    y = min(verifica.braccio_terr_m, geometria.h_muro_tot_m)
    x_muro = _faccia_interna_stem_x(y, inputs)
    x_terreno = geometria.b_fond_m + 0.2
    return Freccia(coda=(x_terreno, y), punta=(x_muro, y), stile="carico",
                    testo=etichetta_quota(etichetta, verifica.sh_terr_kN, "kN", 0))


def _diagramma_pressioni(pressioni_terreno: tuple[PressioniCombo, ...], geometria: GeometriaResult) -> Diagramma:
    governante = max(pressioni_terreno, key=lambda p: max(p.p_valle_kPa, p.p_monte_kPa))
    return Diagramma(
        base=((geometria.b_fond_m, 0.0), (0.0, 0.0)),  # right->left: ordinates hang below the base
        valori=(governante.p_valle_kPa, governante.p_monte_kPa),
        etichette=(etichetta_quota("p_valle", governante.p_valle_kPa, "kPa", 0),
                   etichetta_quota("p_monte", governante.p_monte_kPa, "kPa", 0)),
        stile="pressione",
    )


def _sezione(
    inputs: MuroSostegnoInput, geometria: GeometriaResult, spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...],
) -> Vista:
    scostamento_o = _MARGINE_QUOTA * geometria.b_fond_m
    scostamento_v = _MARGINE_QUOTA * geometria.h_muro_tot_m
    forme = [
        Rettangolo(x=0.0, y=0.0, w=geometria.b_fond_m, h=inputs.s_fond_m, stile="calcestruzzo"),
        _stem(inputs),
        _terreno(inputs, geometria),
        *_sovraccarico(inputs, geometria),
        _diagramma_pressioni(pressioni_terreno, geometria),
        Quota(p1=(0.0, 0.0), p2=(geometria.b_fond_m, 0.0), distanza=-scostamento_o,
              testo=etichetta_quota("B", geometria.b_fond_m, "m")),
        Quota(p1=(0.0, 0.0), p2=(0.0, geometria.h_muro_tot_m), distanza=scostamento_v,
              testo=etichetta_quota("H", geometria.h_muro_tot_m, "m")),
    ]
    statica = _spinta("STR_1", spinte, ribaltamento_scorrimento)
    if statica is not None:
        forme.append(_freccia_spinta(statica, inputs, geometria, etichetta="S_stat"))
    sismica = _spinta("SISMA_1", spinte, ribaltamento_scorrimento)
    if sismica is not None:
        forme.append(_freccia_spinta(sismica, inputs, geometria, etichetta="S_sism"))
    return Vista(titolo="Sezione", forme=tuple(forme))

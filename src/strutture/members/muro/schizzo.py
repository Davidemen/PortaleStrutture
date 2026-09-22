"""Live sketch for `muro-sostegno`: Sezione (stem, heel, toe, backfill, surcharge, static/seismic
thrust arrows at their heights, base-pressure diagram, main dimensions) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + computed results; a failure
here must never fail the calculation (guarded in `tool.run_muro_sostegno`).

Coordinates: x=0 at the toe/valle outer edge (the overturning pole), y=0 at the footing base —
the same reference `geometria_muro` already uses for every centroid."""
from strutture.shared.sketch import (
    Diagramma,
    Etichetta,
    Freccia,
    Linea,
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

_MARGINE_QUOTA = 0.07  # frazione della dimensione maggiore, per lo scostamento delle linee di quota (6-8 %)
_ALTEZZA_RELATIVA_DIAGRAMMA = 0.25  # altezza resa del diagramma delle pressioni (default di Diagramma)
_ALTEZZA_RELATIVA_SOVRACCARICO = 0.12  # banda del sovraccarico: più sottile del diagramma di pressione


def disegna(
    inputs: MuroSostegnoInput, geometria: GeometriaResult, spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...],
) -> Sketch:
    """Sezione trasversale del muro con spinte e diagramma delle pressioni di base."""
    return Sketch(viste=(_sezione(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno),),
                  nota="Schema non in scala")


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


def _sovraccarico(inputs: MuroSostegnoInput, geometria: GeometriaResult) -> tuple:
    """Banda del sovraccarico q sopra il cuneo di terreno (assente se q=0): una `Diagramma`
    uniforme, non una singola freccia senza punta visibile, con un'unica etichetta (valore, il
    simbolo "q" è già reso da `Etichetta`... qui il testo del diagramma include il simbolo perché
    `Diagramma` non ha un campo `simbolo` separato per le sue etichette)."""
    if inputs.q_kN_m2 <= 0:
        return ()
    y_top = inputs.s_fond_m + inputs.h_muro_m
    x_sinistra = _faccia_interna_stem_x(y_top, inputs)
    x_destra = geometria.b_fond_m
    return (Diagramma(
        base=((x_sinistra, y_top), (x_destra, y_top)),  # sinistra->destra: la banda sporge verso l'alto
        valori=(inputs.q_kN_m2, inputs.q_kN_m2),
        etichette=(etichetta_quota("q", inputs.q_kN_m2, "kN/m²", 0), ""),
        stile="carico",
        altezza_relativa=_ALTEZZA_RELATIVA_SOVRACCARICO,
    ),)


def _spinta(nome_cercato: str, spinte: tuple[SpintaCombo, ...],
            ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...]) -> RibaltamentoScorrimentoCombo | None:
    for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True):
        if spinta.nome == nome_cercato:
            return verifica
    return None


def _freccia_spinta(verifica: RibaltamentoScorrimentoCombo, inputs: MuroSostegnoInput,
                     geometria: GeometriaResult, *, etichetta: str) -> tuple[Freccia, Etichetta]:
    """Freccia della spinta (senza testo incorporato: l'etichetta è un `Etichetta` separato, ancorata
    alla coda sul lato libero a destra del cuneo di terreno, cosi' non cade mai sul paramento)."""
    y = min(verifica.braccio_terr_m, geometria.h_muro_tot_m)
    x_muro = _faccia_interna_stem_x(y, inputs)
    x_terreno = geometria.b_fond_m + 0.2
    freccia = Freccia(coda=(x_terreno, y), punta=(x_muro, y), stile="carico")
    testo = Etichetta(punto=(x_terreno, y), simbolo=etichetta, testo=_valore_kN(verifica.sh_terr_kN),
                       ancora="start", stile="carico")
    return freccia, testo


def _valore_kN(valore: float) -> str:
    return f"{valore:.0f} kN"


def _valore_m(valore: float) -> str:
    return f"{valore:.2f} m".replace(".", ",")


def _piano_campagna_valle(inputs: MuroSostegnoInput, geometria: GeometriaResult) -> tuple:
    """HIGH finding: `terreno_profondita_posa_m` (D) è misurata dal piano campagna A VALLE (lato
    mancia): mostrarla nello schizzo, non solo nella descrizione del campo, così un valore riferito
    per errore al piano di campagna a monte (più in alto di h_muro + s_fond) risulta visivamente
    incoerente con l'altezza del muro invece di passare inosservato. Assente quando il blocco
    'Terreno di fondazione' non è compilato."""
    if inputs.terreno_profondita_posa_m is None:
        return ()
    d = inputs.terreno_profondita_posa_m
    x_sinistra = -0.12 * geometria.b_fond_m
    x_destra = inputs.b_valle_m
    return (
        Linea(p1=(x_sinistra, d), p2=(x_destra, d), stile="quota", tratteggio=True),
        Etichetta(punto=(x_sinistra, d), simbolo="D", testo=_valore_m(d), ancora="end", stile="quota"),
    )


def _diagramma_pressioni(pressioni_terreno: tuple[PressioniCombo, ...], geometria: GeometriaResult) -> Diagramma:
    """`base` runs right (x=B, lato monte) -> left (x=0, lato valle): `valori`/`etichette` must be
    ordered the same way (monte first, valle second) so each ordinate lands at the pressure's own
    end, not mirrored across the footing. Zero ends stay unlabelled."""
    governante = max(pressioni_terreno, key=lambda p: max(p.p_valle_kPa, p.p_monte_kPa))
    return Diagramma(
        base=((geometria.b_fond_m, 0.0), (0.0, 0.0)),  # right->left: ordinates hang below the base
        valori=(governante.p_monte_kPa, governante.p_valle_kPa),
        etichette=(_etichetta_pressione("p_monte", governante.p_monte_kPa),
                   _etichetta_pressione("p_valle", governante.p_valle_kPa)),
        stile="pressione",
        altezza_relativa=_ALTEZZA_RELATIVA_DIAGRAMMA,
    )


def _etichetta_pressione(simbolo: str, valore_kPa: float) -> str:
    return etichetta_quota(simbolo, valore_kPa, "kPa", 0) if valore_kPa > 0 else ""


def _sezione(
    inputs: MuroSostegnoInput, geometria: GeometriaResult, spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...],
) -> Vista:
    scostamento_o = _MARGINE_QUOTA * geometria.b_fond_m
    scostamento_v = _MARGINE_QUOTA * geometria.h_muro_tot_m
    # la quota B sta sotto il diagramma delle pressioni (che sporge in basso di ~altezza_relativa
    # del lato minore), non appena sotto la fondazione: altrimenti i due si accavallano.
    sporgenza_diagramma = _ALTEZZA_RELATIVA_DIAGRAMMA * min(geometria.b_fond_m, geometria.h_muro_tot_m)
    forme = [
        Rettangolo(x=0.0, y=0.0, w=geometria.b_fond_m, h=inputs.s_fond_m, stile="calcestruzzo"),
        _stem(inputs),
        _terreno(inputs, geometria),
        *_sovraccarico(inputs, geometria),
        _diagramma_pressioni(pressioni_terreno, geometria),
        Quota(p1=(0.0, 0.0), p2=(geometria.b_fond_m, 0.0), distanza=-(scostamento_o + sporgenza_diagramma),
              testo=etichetta_quota("B", geometria.b_fond_m, "m")),
        Quota(p1=(0.0, 0.0), p2=(0.0, geometria.h_muro_tot_m), distanza=scostamento_v,
              testo=etichetta_quota("H", geometria.h_muro_tot_m, "m"), campo="h_muro_m"),  # H totale: si modifica h_muro
        *_piano_campagna_valle(inputs, geometria),
    ]
    statica = _spinta("STR_1", spinte, ribaltamento_scorrimento)
    if statica is not None:
        forme.extend(_freccia_spinta(statica, inputs, geometria, etichetta="S_stat"))
    sismica = _spinta("SISMA_1", spinte, ribaltamento_scorrimento)
    if sismica is not None:
        forme.extend(_freccia_spinta(sismica, inputs, geometria, etichetta="S_sism"))
    return Vista(titolo="Sezione", forme=tuple(forme))

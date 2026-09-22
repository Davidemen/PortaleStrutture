"""Verified restatement (docs/architecture-phase2.md) of `weighted_es.py` (Step 7, the
depth-weighted average modulus `Es = Σ Ei·Δzi / H`, `shared.soil_layers.weighted_modulus`) and
`settlement_tg.py` (Steps 8-9, `ΔH = q·(B/2 or B)·(1−μ²)/Es·IS·IF·(4 or 1)`). Standard mode only
(this module is never called with `legacy_compat=True`): `(1−μ²)` applies throughout, not the
sheet's `(1−μ)` (`settlement_tg.py`'s own docstring: classical Timoshenko & Goodier theory).

`Es` sums over every soil layer overlapping `[0, H]`, measured from the FOUNDATION BASE
(`ground_to_base.shift_to_base`, an intermediate `TimoshenkoGoodierOutput` does not expose — read
straight from the package's own step function, exactly as the architecture brief allows). Up to 6
layers are traced individually (docs/architecture-phase2.md §5: "many-rows tools trace the
GOVERNING row only"); any remainder is lumped into one step, same convention as
`relazione_newmark_righe.py`.

`ΔH`'s `kPa->MPa` (÷1000) and `m->mm` (×1000) conversions cancel exactly, so the formula below
takes `q` in kPa and `Es` in MPa directly and needs no `scala` (1.0, documented, not omitted)."""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.soil_layers import SoilLayer

from .boundary import to_kpa, to_m
from .ground_to_base import shift_to_base
from .models_tg import TimoshenkoGoodierInput, TimoshenkoGoodierOutput
from .relazione_tg_fattori import b_m_da_inputs, h_m_da_inputs
from .settlement_tg import QUADRANTS_CENTRO

CLAUSOLA_ES = "Timoshenko & Goodier 1970 (media pesata sullo spessore)"
CLAUSOLA_DELTAH = "Timoshenko & Goodier 1970"
_MAX_STRATI_TRACCIATI = 6


def traccia_cedimento(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> Traccia:
    """Fino a 6 passi per gli strati che alimentano Es, il passo Es, e i due cedimenti finali
    ΔH_centro/ΔH_bordo (entrambi highlight)."""
    b_m, h_m = b_m_da_inputs(inputs), h_m_da_inputs(inputs)
    d_m = to_m(inputs.d, inputs.sistema_unita)
    layers = shift_to_base(inputs.strati, d_m)
    overlaps = _overlaps(layers, h_m)
    tracciati = overlaps[:_MAX_STRATI_TRACCIATI]
    resto = overlaps[_MAX_STRATI_TRACCIATI:]

    termini_mpa_m = [layer.modulo_MPa * overlap for layer, overlap in tracciati]
    passi: tuple[Passo, ...] = tuple(
        _passo_strato(i, layer, overlap, h_m) for i, (layer, overlap) in enumerate(tracciati, start=1)
    )
    resto_mpa_m = sum(layer.modulo_MPa * overlap for layer, overlap in resto)
    if resto:
        passi = (*passi, _passo_resto(len(resto), resto_mpa_m))
    passi = (*passi, _passo_es(output, termini_mpa_m, resto_mpa_m if resto else None, h_m))
    passi = (*passi, _passo_deltah_centro(inputs, output, b_m), _passo_deltah_bordo(inputs, output, b_m))
    return Traccia(titolo="Modulo medio pesato e cedimento (Timoshenko & Goodier)", passi=passi)


def _overlaps(layers: tuple[SoilLayer, ...], h_m: float) -> tuple[tuple[SoilLayer, float], ...]:
    """`(layer, overlap_m)` for every layer with a positive overlap with `[0, h_m]`, in the same
    order and with the same early-stop as `shared.soil_layers.weighted_modulus`."""
    risultato: list[tuple[SoilLayer, float]] = []
    covered_to = 0.0
    for layer in layers:
        overlap = min(layer.z_bot_m, h_m) - max(layer.z_top_m, 0.0)
        if overlap > 0:
            risultato.append((layer, overlap))
            covered_to = max(covered_to, min(layer.z_bot_m, h_m))
        if covered_to >= h_m:
            break
    return tuple(risultato)


def _passo_strato(indice: int, layer: SoilLayer, overlap_m: float, h_m: float) -> Passo:
    etichetta = str(indice)
    return Passo(
        simbolo=f"EΔz_{etichetta}", formula=f"E_{etichetta} * Δz_{etichetta}",
        valori=(
            Valore(
                simbolo=f"E_{etichetta}", valore=layer.modulo_MPa, unita="MPa",
                descrizione=f"modulo dello strato {indice} (dalla stratigrafia, riferita al piano di posa: "
                            f"{layer.z_top_m:.4g}-{layer.z_bot_m:.4g} m)",
            ),
            Valore(simbolo=f"Δz_{etichetta}", valore=overlap_m, unita="m", descrizione=f"spessore dello strato {indice} compreso in [0, H={h_m:.4g} m]"),
        ),
        risultato=layer.modulo_MPa * overlap_m, unita="MPa·m",
        nota=f"Contributo dello strato {indice} alla somma pesata Σ Ei·Δzi.",
    )


def _passo_resto(n_restanti: int, resto_mpa_m: float) -> Passo:
    return Passo(
        simbolo="Σresto", formula="Σresto",
        valori=(
            Valore(
                simbolo="Σresto", valore=resto_mpa_m, unita="MPa·m",
                descrizione=f"somma di Ei·Δzi sui restanti {n_restanti} strati compresi in [0, H], stesso procedimento "
                            "dei passi precedenti, non elencati singolarmente qui",
            ),
        ),
        risultato=resto_mpa_m, unita="MPa·m",
        nota=f"Somma dei {n_restanti} strati intermedi non mostrati singolarmente.",
    )


def _passo_es(output: TimoshenkoGoodierOutput, termini_mpa_m: list[float], resto_mpa_m: float | None, h_m: float) -> Passo:
    etichette = [str(i) for i in range(1, len(termini_mpa_m) + 1)]
    identificatori = [f"EΔz_{e}" for e in etichette]
    valori = [
        Valore(simbolo=identificatore, valore=valore, unita="MPa·m", descrizione="calcolato sopra")
        for identificatore, valore in zip(identificatori, termini_mpa_m, strict=True)
    ]
    if resto_mpa_m is not None:
        identificatori.append("Σresto")
        valori.append(Valore(simbolo="Σresto", valore=resto_mpa_m, unita="MPa·m", descrizione="calcolato sopra"))
    valori.append(Valore(simbolo="H", valore=h_m, unita="m", descrizione="profondità significativa"))
    formula = f"({' + '.join(identificatori)}) / H"
    return Passo(
        simbolo="Es", formula=formula, valori=tuple(valori),
        risultato=output.modulo.es_MPa, unita="MPa", clausola=CLAUSOLA_ES,
        nota="Modulo elastico medio pesato sullo spessore, su [0, H].",
    )


def _passo_deltah_centro(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput, b_m: float) -> Passo:
    fattori, modulo, cedimento = output.fattori, output.modulo, output.cedimento
    formula = f"q * (B / 2) * (1 - μ^2) / Es * IS_centro * IF_centro * {QUADRANTS_CENTRO:g}"
    return Passo(
        simbolo="ΔH_centro", formula=formula,
        valori=(
            Valore(simbolo="q", valore=to_kpa(inputs.q, inputs.sistema_unita), unita="kPa", descrizione="pressione di contatto uniforme in fondazione"),
            Valore(simbolo="B", valore=b_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="μ", valore=inputs.mu, descrizione="coefficiente di Poisson del terreno"),
            Valore(simbolo="Es", valore=modulo.es_MPa, unita="MPa", descrizione="modulo medio pesato, calcolato sopra"),
            Valore(simbolo="IS_centro", valore=fattori.is_centro, descrizione="fattore di influenza allo spostamento, calcolato sopra"),
            Valore(simbolo="IF_centro", valore=fattori.if_centro, descrizione="fattore di forma/profondità, letto dal grafico (Fig. 3) — dato d'ingresso"),
        ),
        risultato=cedimento.delta_h_centro_mm, unita="mm", clausola=CLAUSOLA_DELTAH,
        nota=f"Cedimento immediato al centro fondazione: superposizione a {QUADRANTS_CENTRO:g} quadranti uguali. "
             "q in kPa ed Es in MPa: le conversioni kPa→MPa e m→mm si semplificano esattamente (fattore 1).",
    )


def _passo_deltah_bordo(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput, b_m: float) -> Passo:
    fattori, modulo, cedimento = output.fattori, output.modulo, output.cedimento
    formula = "q * B * (1 - μ^2) / Es * IS_bordo * IF_bordo"
    return Passo(
        simbolo="ΔH_bordo", formula=formula,
        valori=(
            Valore(simbolo="q", valore=to_kpa(inputs.q, inputs.sistema_unita), unita="kPa"),
            Valore(simbolo="B", valore=b_m, unita="m"),
            Valore(simbolo="μ", valore=inputs.mu),
            Valore(simbolo="Es", valore=modulo.es_MPa, unita="MPa", descrizione="modulo medio pesato, calcolato sopra"),
            Valore(simbolo="IS_bordo", valore=fattori.is_bordo, descrizione="fattore di influenza allo spostamento, calcolato sopra"),
            Valore(simbolo="IF_bordo", valore=fattori.if_bordo, descrizione="fattore di forma/profondità, letto dal grafico (Fig. 3) — dato d'ingresso"),
        ),
        risultato=cedimento.delta_h_bordo_mm, unita="mm", clausola=CLAUSOLA_DELTAH,
        nota="Cedimento immediato al punto medio del bordo: nessuna superposizione a quadranti, un solo semipiano (Timoshenko & Goodier).",
    )

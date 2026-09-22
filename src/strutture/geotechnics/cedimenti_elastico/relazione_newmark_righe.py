"""Shared per-slice tracer for every Newmark integration path (CENTRO main, PUNTO O, PUNTO O') —
`integrate.py`'s `Δw = Δz·(Δσz/1000)/E`, summed to `w` (`docs/specs/geo-cedimenti-elastico.md`
Tool 1, "Shared sub-routine"). Up to 3 representative slices are traced individually
(docs/architecture-phase2.md §5: "many-rows tools trace the GOVERNING row only"), plus one step
lumping every remaining slice's already-computed `delta_w_m` (never re-derived, just summed in
Python from the output rows — the calculation code itself is not touched), so the total reproduces
the tool's ACTUAL sum, not an approximation of it — same convention as `cedimenti_edometrico.
relazione_cedimento`.

Standard mode (`integrate.py`, never `legacy_compat=True`) evaluates `Δσz` at each slice's
MID-depth `(z_prec+z)/2`, not at the reported `z_m` (the slice bottom) — the second alternative
`docs/architecture-phase2.md` §6 names for the geotechnics packages ("the stress at each layer
mid-depth"), stated explicitly in every row's `nota` below so it is never a silent surprise.

`Δw`'s formula prints the `/1000` (kPa→MPa) conversion IN THE FORMULA, exactly as `integrate.py`'s
own `Δz·(Δσz/1000)/E` does: the previous version pre-divided the `Δσz` Valore silently (49,03 kPa
re-entering the next line as 0,04903 with no visible factor) — the sibling `cedimenti_edometrico`
tool always prints its own scale factors, so this one now does too (review finding MISLEADING).
`Δwresto`'s `simbolo` carries the lumped slice count and depth range (review finding MISSING_STEP,
same fix as `cedimenti_edometrico.relazione_cedimento._passo_resto`: `nota` is never rendered by
`traccia_a_testo`)."""
from collections.abc import Callable

from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import KPA_PER_MPA, MM_PER_M

from .models_newmark import RigaNewmark

_MAX_FETTE_TRACCIATE = 3
FormulaSigma = Callable[[RigaNewmark, float, str], tuple[str, tuple[Valore, ...], str]]


def traccia_fette(
    titolo: str, righe: tuple[RigaNewmark, ...], simbolo_totale: str, valore_totale_mm: float,
    formula_sigma: FormulaSigma, clausola: str,
) -> Traccia:
    indici = _indici_rappresentativi(len(righe))
    tracciate = tuple(righe[i] for i in indici)
    precedenti = tuple(righe[i - 1].z_m if i > 0 else 0.0 for i in indici)

    passi: tuple[Passo, ...] = ()
    for posizione, (riga, z_prec) in enumerate(zip(tracciate, precedenti, strict=True), start=1):
        etichetta = str(posizione)
        formula, valori_sigma, nota_sigma = formula_sigma(riga, z_prec, etichetta)
        passi = (
            *passi,
            Passo(
                simbolo=f"Δσz_{etichetta}", formula=formula, valori=valori_sigma,
                risultato=riga.delta_sigma_kPa, unita="kPa", clausola=clausola, nota=nota_sigma,
            ),
            _passo_delta_w(riga, z_prec, etichetta),
        )

    indici_tracciati = set(indici)
    lumped = tuple(r for i, r in enumerate(righe) if i not in indici_tracciati)
    resto_m = sum(r.delta_w_m for r in lumped)
    if lumped:
        passi = (*passi, _passo_resto(lumped, resto_m))
    passi = (*passi, _passo_totale(simbolo_totale, tracciate, resto_m if lumped else None, valore_totale_mm, clausola))
    return Traccia(titolo=titolo, passi=passi)


def _indici_rappresentativi(n: int) -> tuple[int, ...]:
    if n <= 0:
        return ()
    if n <= _MAX_FETTE_TRACCIATE:
        return tuple(range(n))
    return (0, n // 2, n - 1)


def _passo_delta_w(riga: RigaNewmark, z_prec: float, etichetta: str) -> Passo:
    assert riga.modulo_MPa is not None  # una run riuscita in modalità standard non può avere E assente
    dz_m = riga.z_m - z_prec
    return Passo(
        simbolo=f"Δw_{etichetta}", formula=f"Δz * Δσz / {KPA_PER_MPA:g} / E",
        valori=(
            Valore(simbolo="Δz", valore=dz_m, unita="m", descrizione=f"spessore della fetta, da z={_testo(z_prec)} a z={_testo(riga.z_m)} m"),
            Valore(simbolo="Δσz", valore=riga.delta_sigma_kPa, unita="kPa", descrizione="incremento di tensione, calcolato sopra"),
            Valore(simbolo="E", valore=riga.modulo_MPa, unita="MPa", descrizione="modulo elastico dello strato applicabile a questa profondità (dalla stratigrafia)"),
        ),
        risultato=riga.delta_w_m, unita="m",
        nota=f"Contributo della fetta a z={_testo(riga.z_m)} m al cedimento (conversione kPa→MPa esplicita nella formula).",
    )


def _passo_resto(lumped: tuple[RigaNewmark, ...], resto_m: float) -> Passo:
    n_restanti = len(lumped)
    z_min, z_max = _testo(lumped[0].z_m), _testo(lumped[-1].z_m)
    simbolo = f"Δwresto  (Σ Δz·Δσz/E, {n_restanti} fette, z={z_min}…{z_max} m)"
    return Passo(
        simbolo=simbolo, formula="Δwresto",
        valori=(
            Valore(
                simbolo="Δwresto", valore=resto_m, unita="m",
                descrizione=f"somma di Δz·Δσz/E sulle restanti {n_restanti} fette di profondità, stesso procedimento "
                            "dei passi precedenti, non elencate singolarmente qui",
            ),
        ),
        risultato=resto_m, unita="m",
        nota=f"Somma delle {n_restanti} fette di profondità intermedie (z={z_min}…{z_max} m) non mostrate singolarmente.",
    )


def _passo_totale(simbolo: str, tracciate: tuple[RigaNewmark, ...], resto_m: float | None, valore_mm: float, clausola: str) -> Passo:
    etichette = [str(i) for i in range(1, len(tracciate) + 1)]
    identificatori = [f"Δw_{e}" for e in etichette]
    valori = [
        Valore(simbolo=f"Δw_{e}", valore=riga.delta_w_m, unita="m", descrizione="calcolato sopra")
        for e, riga in zip(etichette, tracciate, strict=True)
    ]
    if resto_m is not None:
        identificatori.append("Δwresto")
        valori.append(Valore(simbolo="Δwresto", valore=resto_m, unita="m", descrizione="calcolato sopra"))
    formula = " + ".join(identificatori) if identificatori else "0"
    return Passo(
        simbolo=simbolo, formula=formula, valori=tuple(valori),
        risultato=valore_mm, unita="mm", scala=MM_PER_M, clausola=clausola,
        nota="Cedimento elastico totale, somma delle fette di profondità.",
    )


def _testo(valore_m: float) -> str:
    return f"{valore_m:.4g}".replace(".", ",")

"""Verified restatement (docs/architecture-phase2.md) of `tensione_indotta.py` (Step 3, the load
spread) and `righe.py`/`cedimento.py` (Steps 5+7, the oedometric strain increment ΔH,i =
Δz·Δσv,q/Eed and its running sum). The full depth grid of `EdometricoOutput.righe` is up to 501
rows (`docs/architecture-phase2.md` §5: "many-rows tools trace the GOVERNING row only") — up to 3
representative slices are traced individually here, exactly as `docs/specs/geo-cedimenti-
edometrico.md`'s own "Representative rows" table does (z=0,10cm; a mid-table depth; the last
slice), plus one step lumping every remaining slice's already-computed `delta_h_cm` (never
re-derived, just summed in Python from `output.righe` — the calculation code itself is not
touched) so the final total step reproduces the tool's ACTUAL sum, not an approximation of it.

`metodo_tensioni="approssimato"` (the tool's example) restates the 2:1-type spread formula
(`shared.soil_stress.spread.spread_2to1`) exactly; `metodo_tensioni="newmark"` cannot be restated
as one closed-form expression in the notation grammar (the exact Newmark/Boussinesq corner-stress
factor needs a branch correction on the arctangent term, `shared.soil_stress.newmark.newmark_corner`
docstring) — that branch cites the already-computed value directly, the identity form the
architecture brief allows for a value the trace does not itself derive.

Neither Δσ (2:1 spread / Newmark-Boussinesq) nor ΔH (one-dimensional oedometric compression) is an
NTC2018 §6.2.2 formula: that clause prescribes WHICH checks must be performed (SLE settlements),
not these classical geotechnical methods — the `clausola` of every row below names the method
itself, the same honesty the sibling `cedimenti_elastico` tools already have for their own methods
("Newmark 1942 (integrazione numerica, Poulos & Davis)", "Timoshenko & Goodier 1970 / Steinbrenner")
(review finding WRONG_CLAUSE)."""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import CM_PER_M, MM_PER_CM

from .ingresso import IngressoSI, converti_in_si
from .models import EdometricoInput
from .output import EdometricoOutput
from .righe import RigaResult

CLAUSOLA_2A1 = "diffusione 2:1 (metodo approssimato)"
CLAUSOLA_NEWMARK = "Newmark 1942 / Boussinesq (integrazione numerica, Poulos & Davis)"
CLAUSOLA_EDOMETRICA = "compressione edometrica monodimensionale (Terzaghi)"
_MAX_FETTE_TRACCIATE = 3  # + il resto lumped in 1 passo: "trace the layers... max 6" passi totali


def traccia_cedimento(inputs: EdometricoInput, output: EdometricoOutput) -> Traccia:
    """Fino a 3 coppie di passi Δσ/ΔH,i (una per fetta rappresentativa), il passo che somma le
    fette restanti, e il cedimento edometrico totale w_ed (Check-free: docs/specs/geo-cedimenti-
    edometrico.md, "nessuna cella di verifica pass/fail esiste in questo foglio")."""
    si = converti_in_si(inputs)
    non_degeneri = _fette_non_degeneri(output)
    indici = _indici_rappresentativi(len(non_degeneri))
    tracciate = tuple(non_degeneri[i] for i in indici)
    precedenti = tuple(non_degeneri[i - 1] if i > 0 else _fetta_zero(output) for i in indici)

    passi: tuple[Passo, ...] = ()
    for posizione, (riga, precedente) in enumerate(zip(tracciate, precedenti, strict=True), start=1):
        etichetta = str(posizione)
        passi = (*passi, _passo_delta_sigma(inputs, si, output, riga, etichetta), _passo_delta_h(riga, precedente, etichetta))

    indici_tracciati = set(indici)
    lumped = tuple(riga for i, riga in enumerate(non_degeneri) if i not in indici_tracciati)
    resto_cm = sum(riga.delta_h_cm for riga in lumped)
    if lumped:
        passi = (*passi, _passo_resto(lumped, resto_cm))
    n_restanti = len(lumped)
    passi = (*passi, _passo_totale(output, tracciate, resto_cm if n_restanti > 0 else None))
    return Traccia(titolo="Cedimento per fette di profondità fino a Z,crit", passi=passi)


def _fette_non_degeneri(output: EdometricoOutput) -> tuple[RigaResult, ...]:
    """Le fette coperte (z < Z,crit) escludendo la prima (z=0), sempre degenere: ΔH_0=0 per
    definizione (nessuna profondità precedente, `righe._incremento_m`), non per la formula
    generale Δz·Δσv,q/Eed."""
    z_crit_m = output.profondita_critica.z_crit_utilizzato_m
    coperte = tuple(riga for riga in output.righe if riga.z_m < z_crit_m)
    return coperte[1:] if coperte and coperte[0].z_m == 0.0 else coperte


def _fetta_zero(output: EdometricoOutput) -> RigaResult:
    return output.righe[0]


def _indici_rappresentativi(n: int) -> tuple[int, ...]:
    """Fino a `_MAX_FETTE_TRACCIATE` indici distinti su `n` fette non degeneri: tutte se poche,
    altrimenti la prima, una centrale e l'ultima."""
    if n <= 0:
        return ()
    if n <= _MAX_FETTE_TRACCIATE:
        return tuple(range(n))
    return (0, n // 2, n - 1)


def _passo_delta_sigma(
    inputs: EdometricoInput, si: IngressoSI, output: EdometricoOutput, riga: RigaResult, etichetta: str,
) -> Passo:
    if inputs.metodo_tensioni == "approssimato":
        formula = "q' * B * L / ((B + z) * (L + z))"
        valori = (
            Valore(simbolo="q'", valore=output.carico.q_prime_kPa, unita="kPa", descrizione="pressione netta di progetto, calcolata sopra"),
            Valore(simbolo="B", valore=si.b_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="L", valore=si.l_m, unita="m", descrizione="lunghezza della fondazione"),
            Valore(simbolo="z", valore=riga.z_m, unita="m", descrizione="profondità dal piano di posa di questa fetta"),
        )
        nota = "Diffusione approssimata del carico (tipo 2:1) sotto il centro dell'area caricata."
        clausola = CLAUSOLA_2A1
    else:
        formula = "Δσ_Newmark"
        valori = (
            Valore(
                simbolo="Δσ_Newmark", valore=riga.delta_sigma_kPa, unita="kPa",
                descrizione="integrale esatto di Newmark/Boussinesq sotto il centro dell'area caricata (Poulos & Davis)",
            ),
        )
        nota = (
            "Calcolato da soil_stress.under_center: la correzione di ramo dell'arcotangente non è "
            "restituita qui in forma chiusa (vedi il modulo)."
        )
        clausola = CLAUSOLA_NEWMARK
    return Passo(
        simbolo=f"Δσ_{etichetta}", formula=formula, valori=valori,
        risultato=riga.delta_sigma_kPa, unita="kPa", clausola=clausola,
        nota=f"Incremento di tensione verticale indotto dal carico a z={_testo_m(riga.z_m)} m. {nota}",
    )


def _passo_delta_h(riga: RigaResult, precedente: RigaResult, etichetta: str) -> Passo:
    dz_m = riga.z_m - precedente.z_m
    assert riga.eed_kPa is not None  # una run riuscita in modalità standard non può avere Eed assente
    return Passo(
        simbolo=f"ΔH_{etichetta}", formula="Δz * Δσ / E_ed",
        valori=(
            Valore(simbolo="Δz", valore=dz_m, unita="m", descrizione=f"spessore della fetta, da z={_testo_m(precedente.z_m)} a z={_testo_m(riga.z_m)} m"),
            Valore(simbolo="Δσ", valore=riga.delta_sigma_kPa, unita="kPa", descrizione="incremento di tensione, calcolato sopra"),
            Valore(simbolo="E_ed", valore=riga.eed_kPa, unita="kPa", descrizione="modulo edometrico dello strato applicabile a questa profondità (dalla stratigrafia)"),
        ),
        risultato=riga.delta_h_cm, unita="cm", scala=CM_PER_M, clausola=CLAUSOLA_EDOMETRICA,
        nota=f"Incremento di cedimento della fetta a z={_testo_m(riga.z_m)} m.",
    )


def _passo_resto(lumped: tuple[RigaResult, ...], resto_cm: float) -> Passo:
    # Conteggio e intervallo di profondità nel simbolo stampato, non solo nella nota (che
    # `traccia_a_testo` non stampa mai): senza, il numero che pesa per la quasi totalità del
    # cedimento totale non era riproducibile (review finding MISSING_STEP).
    n_restanti = len(lumped)
    z_min, z_max = _testo_m(lumped[0].z_m), _testo_m(lumped[-1].z_m)
    simbolo = f"ΔH_resto  (Σ Δz·Δσ/E_ed, {n_restanti} fette, z={z_min}…{z_max} m)"
    return Passo(
        simbolo=simbolo, formula="ΔH_resto",
        valori=(
            Valore(
                simbolo="ΔH_resto", valore=resto_cm, unita="cm",
                descrizione=f"somma di Δz·Δσv,q/Eed sulle restanti {n_restanti} fette di profondità fino a Z,crit, "
                            "stesso procedimento dei passi precedenti, non elencate singolarmente qui",
            ),
        ),
        risultato=resto_cm, unita="cm", clausola=CLAUSOLA_EDOMETRICA,
        nota=f"Somma delle {n_restanti} fette di profondità intermedie (z={z_min}…{z_max} m) non mostrate singolarmente.",
    )


def _passo_totale(output: EdometricoOutput, tracciate: tuple[RigaResult, ...], resto_cm: float | None) -> Passo:
    etichette = [str(i) for i in range(1, len(tracciate) + 1)]
    termini = [f"ΔH_{e}" for e in etichette]
    valori = [
        Valore(simbolo=f"ΔH_{e}", valore=riga.delta_h_cm, unita="cm", descrizione="calcolato sopra")
        for e, riga in zip(etichette, tracciate, strict=True)
    ]
    if resto_cm is not None:
        termini.append("ΔH_resto")
        valori.append(Valore(simbolo="ΔH_resto", valore=resto_cm, unita="cm", descrizione="calcolato sopra"))
    formula = " + ".join(termini) if termini else "0"
    return Passo(
        simbolo="w_ed", formula=formula, valori=tuple(valori),
        risultato=output.cedimento.w_ed_mm, unita="mm", scala=MM_PER_CM, clausola=CLAUSOLA_EDOMETRICA,
        nota="Cedimento edometrico totale, somma delle fette di profondità fino a Z,crit.",
    )


def _testo_m(valore_m: float) -> str:
    return f"{valore_m:.4g}".replace(".", ",")

"""Verified restatement of `sisma-vita-riferimento` (NTC2018 §2.4.3, §3.2.1 eq. 3.2.1;
docs/architecture-phase2.md §6, wave 3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package — and of the shared
`strutture.shared.ntc_site_seismic` chain it wraps — is never touched, not one number.

`Cu` (Tabelle!C2:F3, NTC2018 Tab. 2.4.II) and `zona_sismica` (comuni database) are table lookups,
not formulas the notation grammar can restate (docs/architecture-phase2.md §2 is a whitelist of
arithmetic operators and functions, no table interpolation): each gets a short Passo of its own
whose `formula` is the identifier itself, naming the table/source in `nota` — the pattern
docs/architecture-phase2.md §6 prescribes for a lookup-only value.

`Provincia`/`Regione` (also comuni-database lookups) are TEXT, not numbers — `Valore`/`Passo` can
only carry a `float` (docs/architecture-phase2.md §1) — so they are administrative context, never
part of this numeric trace; only the already-numeric `zona_sismica` is restated.

Each `T_R` (periodo di ritorno) gets TWO Passo, mirroring `V_R,0`/`V_R` and `S_s,0`/`S_s`: a
`T_R,{stato},0` restating NTC2018 eq. 3.2.1 exactly, and a final `T_R,{stato}` rounded to the
nearest year — `periodo_ritorno` applies that rounding for display, but the notation grammar has
no `round` function (docs/architecture-phase2.md §2) and the calculation code must not change, so
the final step uses the "formula = the identifier itself" pattern of a lookup-only value (§6):
`traccia_a_testo` prints no `nota` (only `passo_a_testo`'s three lines), so the rounding must be
its own visible step, not a note the reviewer reading the plain-text trace would never see.
"""
import math

from strutture.shared.ntc_site_seismic import periodo_ritorno
from strutture.shared.ntc_site_seismic.tables import COEFFICIENTE_USO, PROBABILITA_SUPERAMENTO_PVR
from strutture.shared.ntc_site_seismic.vita_riferimento import VITA_RIFERIMENTO_MINIMA_ANNI
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.tables import exact_lookup

from .models import SismaVitaRiferimentoInput, SismaVitaRiferimentoOutput, StatoLimite

_TABELLA_CU_TESTO = "; ".join(f"{classe}={valore:g}" for classe, valore in COEFFICIENTE_USO)


def relazione_vita_riferimento(
    inputs: SismaVitaRiferimentoInput, output: SismaVitaRiferimentoOutput
) -> tuple[Traccia, ...]:
    """12 (senza comune: 11) passi in una Traccia: C_u, V_R (grezzo + con minimo), gli 8 T_R
    (grezzo + arrotondato per ciascuno dei 4 stati limite), ed eventualmente la zona sismica del
    comune indicato."""
    vr_grezzo = inputs.vn_anni * output.vita.cu
    passi = (
        _passo_cu(inputs, output),
        _passo_vr_grezzo(inputs, output, vr_grezzo),
        _passo_vr(output, vr_grezzo),
        *(passo for stato in ("SLO", "SLD", "SLV", "SLC") for passo in _passi_tr(output, stato)),
    )
    if output.comune_info is not None:
        passi = (*passi, _passo_zona_sismica(output))
    return (Traccia(titolo="Vita di riferimento e periodi di ritorno", passi=passi),)


def _passo_cu(inputs: SismaVitaRiferimentoInput, output: SismaVitaRiferimentoOutput) -> Passo:
    return Passo(
        simbolo="C_u",
        formula="C_u",
        valori=(Valore(simbolo="C_u", valore=output.vita.cu, descrizione=f"coefficiente d'uso per classe d'uso {inputs.classe_uso}"),),
        risultato=output.vita.cu, unita="-", clausola="NTC2018 §2.4.2 Tab. 2.4.II",
        nota=f"Tabelle!C2:F3 (NTC2018 Tab. 2.4.II), coefficiente d'uso per classe d'uso: {_TABELLA_CU_TESTO}.",
    )


def _passo_vr_grezzo(inputs: SismaVitaRiferimentoInput, output: SismaVitaRiferimentoOutput, vr_grezzo: float) -> Passo:
    return Passo(
        simbolo="V_R,0",
        formula="V_N * C_u",
        valori=(
            Valore(simbolo="V_N", valore=inputs.vn_anni, unita="anni", descrizione="vita nominale della costruzione"),
            Valore(simbolo="C_u", valore=output.vita.cu, descrizione="coefficiente d'uso, calcolato sopra"),
        ),
        risultato=vr_grezzo, unita="anni", clausola="NTC2018 §2.4.3",
        nota="Vita di riferimento, prima del minimo di legge.",
    )


def _passo_vr(output: SismaVitaRiferimentoOutput, vr_grezzo: float) -> Passo:
    return Passo(
        simbolo="V_R",
        formula=f"max(V_R,0, {VITA_RIFERIMENTO_MINIMA_ANNI:g})",
        valori=(Valore(simbolo="V_R,0", valore=vr_grezzo, descrizione="vita di riferimento grezza, calcolata sopra"),),
        risultato=output.vita.vr, unita="anni", clausola="NTC2018 §2.4.3",
        nota=f"La vita di riferimento non può essere inferiore a {VITA_RIFERIMENTO_MINIMA_ANNI:g} anni.",
    )


def _passi_tr(output: SismaVitaRiferimentoOutput, stato: StatoLimite) -> tuple[Passo, Passo]:
    pvr = exact_lookup(PROBABILITA_SUPERAMENTO_PVR, stato)
    vr = output.vita.vr
    grezzo = -vr / math.log(1 - pvr)
    arrotondato = float(periodo_ritorno(vr, stato))
    passo_grezzo = Passo(
        simbolo=f"T_R,{stato},0",
        formula=f"-V_R / ln(1 - {pvr:g})",
        valori=(Valore(simbolo="V_R", valore=vr, unita="anni", descrizione="vita di riferimento, calcolata sopra"),),
        risultato=grezzo, unita="anni", clausola="NTC2018 §3.2.1 eq. 3.2.1",
        nota=f"Probabilità di superamento P_VR={pvr:g} per lo stato limite {stato} (NTC2018 §3.2.1).",
    )
    passo_arrotondato = Passo(
        simbolo=f"T_R,{stato}",
        formula=f"T_R,{stato}",
        valori=(Valore(simbolo=f"T_R,{stato}", valore=arrotondato, unita="anni", descrizione="valore grezzo, calcolato sopra, arrotondato all'anno più vicino"),),
        risultato=arrotondato, unita="anni", clausola="NTC2018 §3.2.1 eq. 3.2.1",
        nota=f"Periodo di ritorno per lo stato limite {stato}, arrotondato all'anno più vicino (come nel foglio originale, ROUND).",
    )
    return (passo_grezzo, passo_arrotondato)


def _passo_zona_sismica(output: SismaVitaRiferimentoOutput) -> Passo:
    comune_info = output.comune_info
    assert comune_info is not None
    return Passo(
        simbolo="zona sismica",
        formula="Zona",
        valori=(Valore(simbolo="Zona", valore=float(comune_info.zona_sismica), descrizione="zona sismica del comune indicato (1 = più severa)"),),
        risultato=float(comune_info.zona_sismica), unita="-",
        nota="Lettura dalla banca dati dei comuni (non dal foglio Sisma, che non ha una colonna zona sismica).",
    )

"""Optional bearing-capacity verification of the foundation soil ('Terreno di fondazione' block),
wired into `muro-sostegno` — split out of `tool.py`, regola dura 12 dei moduli piccoli.
"""
import math

from strutture.shared.divergences import legacy
from strutture.shared.report import Check

from .capacita_portante_fondazione import capacita_portante_combo
from .capacita_portante_muro_costanti import (
    AVVISO_CAPACITA_PORTANTE,
    AVVISO_CAPACITA_PORTANTE_SISMICA,
    AVVISO_ECCENTRICITA_LIMITE,
    AVVISO_TERRENO_IGNORATO_LEGACY,
    CLAUSE_CAPACITA_PORTANTE,
    CLAUSE_CAPACITA_PORTANTE_SISMICA,
    COMBO_CAPACITA_PORTANTE,
    GAMMA_R_CAPACITA_PORTANTE_SISMA,
    GAMMA_R_CAPACITA_PORTANTE_STATICO,
    SOGLIA_PROFONDITA_POSA_SOSPETTA_M,
)
from .models import (
    CapacitaPortanteCombo,
    CapacitaPortanteFondazioneResult,
    GeometriaResult,
    MuroSostegnoInput,
    PressioniCombo,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)
from .ribaltamento_scorrimento import forze_normale_tangente_base

# Re-exported for backward compatibility (some callers import the constants from this module).
__all__ = [
    "AVVISO_CAPACITA_PORTANTE",
    "AVVISO_CAPACITA_PORTANTE_SISMICA",
    "AVVISO_ECCENTRICITA_LIMITE",
    "AVVISO_TERRENO_IGNORATO_LEGACY",
    "esito_capacita_portante",
]


def _avviso_profondita_posa_implausibile(d_m: float, h_muro_m: float) -> str | None:
    if d_m <= h_muro_m or d_m <= SOGLIA_PROFONDITA_POSA_SOSPETTA_M:
        return None
    return (
        f"Profondità di posa D={d_m:.2f} m maggiore dell'altezza fuori terra del muro "
        f"(h_muro={h_muro_m:.2f} m): controlla che D sia misurata dal piano campagna a VALLE (lato "
        "mancia), non dal piano campagna a monte/tacco (più in alto di h_muro + s_fond)."
    )


def _capacita_portante_riga(
    spinta: SpintaCombo, verifica: RibaltamentoScorrimentoCombo, pressioni: PressioniCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult
) -> CapacitaPortanteCombo:
    gamma_r = GAMMA_R_CAPACITA_PORTANTE_SISMA if spinta.sismica else GAMMA_R_CAPACITA_PORTANTE_STATICO
    # HIGH finding: la base di fondazione puo' essere inclinata di `omega_deg` (gia' un input,
    # gia' usato dalla verifica a scorrimento). EN1997-1 Annesso D richiede H/V relativi alla base
    # quando questa e' inclinata (non Ntot/Rtot globali): stessa scomposizione, gia' collaudata,
    # di `fattore_sicurezza_scorrimento`.
    omega_rad = math.radians(inputs.omega_deg)
    normale_kn, tangente_kn = forze_normale_tangente_base(n_tot_kN=verifica.n_tot_kN, r_tot_kN=verifica.r_tot_kN, omega_rad=omega_rad)
    return capacita_portante_combo(
        spinta.nome,
        condizione=inputs.terreno_condizione,
        b_fond_m=geometria.b_fond_m,
        eccentricita_m=pressioni.eccentricita_m,
        n_ed_kn=normale_kn,
        h_kn=abs(tangente_kn),
        profondita_posa_m=inputs.terreno_profondita_posa_m,
        gamma_kn_m3=inputs.terreno_gamma_kn_m3,
        profondita_falda_m=inputs.terreno_profondita_falda_m,
        phi_k_deg=inputs.terreno_phi_k_deg,
        c_k_kpa=inputs.terreno_c_k_kpa,
        cu_k_kpa=inputs.terreno_cu_k_kpa,
        gamma_r=gamma_r,
        alpha_base_deg=inputs.omega_deg,
    )


def _run_capacita_portante_fondazione(
    spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...],
    pressioni_terreno: tuple[PressioniCombo, ...],
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
) -> CapacitaPortanteFondazioneResult:
    # HIGH finding: solo le righe A1+M1 (STR_1/STR_2, coerenti con i parametri caratteristici non
    # ridotti usati sotto) e le sismiche (gamma_R dedicato) entrano in questa verifica — vedi
    # `COMBO_CAPACITA_PORTANTE` (costanti) per il perche' GEO_1/GEO_2/EQU_1/EQU_2 restano escluse.
    combinazioni = tuple(
        _capacita_portante_riga(spinta, verifica, pressioni, inputs=inputs, geometria=geometria)
        for spinta, verifica, pressioni in zip(spinte, ribaltamento_scorrimento, pressioni_terreno, strict=True)
        if spinta.nome in COMBO_CAPACITA_PORTANTE
    )
    governante = max(combinazioni, key=lambda c: c.rapporto)
    # MEDIUM finding: la riga governante sismica usa la stessa formula statica dell'Annesso D
    # senza la riduzione inerziale (Paolucci-Pecker, §7.11.5.3.1/§7.11.6.2.1): il Check deve citare
    # quella clausola e segnalare l'esito come da confermare, non come un ordinario passato/fallito.
    sismica = governante.nome.startswith("SISMA")
    detail = f"N_Ed/R_d={governante.rapporto:.3f} sulla combinazione governante {governante.nome}"
    if sismica:
        detail += " — esito da confermare: coefficienti sismici (Paolucci-Pecker) non applicati"
    verifica = Check(
        name="Capacità portante del terreno di fondazione",
        passed=governante.rapporto <= 1.0,
        detail=detail,
        clause=CLAUSE_CAPACITA_PORTANTE_SISMICA if sismica else CLAUSE_CAPACITA_PORTANTE,
        value=governante.rapporto,
        limit=1.0,
        unit="-",
    )
    return CapacitaPortanteFondazioneResult(
        combinazioni=combinazioni, combo_governante=governante.nome, rapporto_governante=governante.rapporto, verifica=verifica,
    )


def esito_capacita_portante(
    spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...],
    pressioni_terreno: tuple[PressioniCombo, ...],
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
) -> tuple[CapacitaPortanteFondazioneResult | None, tuple[Check, ...], tuple[str, ...]]:
    """Wires the optional 'Terreno di fondazione' block into the report (docs/architecture-phase4.md
    §C "Integration"): block empty -> today's behaviour unchanged (AVVISO_CAPACITA_PORTANTE, no
    check); block filled + legacy_compat -> ignored, with a dedicated warning on top; block filled
    in standard mode -> the "non calcolata" sentence drops out (it IS calculated now) but the
    eccentricity caveat (MEDIUM finding: this check still has no e/B limit of its own) stays."""
    if inputs.terreno_condizione is None:
        return None, (), (AVVISO_CAPACITA_PORTANTE,)
    if legacy("muro-sostegno/verifica-portanza-non-segnalata", inputs.legacy_compat):
        return None, (), (AVVISO_CAPACITA_PORTANTE, AVVISO_TERRENO_IGNORATO_LEGACY)
    risultato = _run_capacita_portante_fondazione(spinte, ribaltamento_scorrimento, pressioni_terreno, inputs=inputs, geometria=geometria)
    avvisi = (AVVISO_ECCENTRICITA_LIMITE, AVVISO_CAPACITA_PORTANTE_SISMICA)
    avviso_profondita = _avviso_profondita_posa_implausibile(inputs.terreno_profondita_posa_m, inputs.h_muro_m)
    if avviso_profondita is not None:
        avvisi = (avviso_profondita, *avvisi)
    return risultato, (risultato.verifica,), avvisi

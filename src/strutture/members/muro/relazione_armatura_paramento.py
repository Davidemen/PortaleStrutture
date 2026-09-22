"""Verified restatement (docs/architecture-phase2.md) of `armatura_paramento.py` (stem bending +
required reinforcement, NTC2018 §6.5.3.1.1/§4.1.2) for the combination that governs THIS design
(`ArmaturaParamentoResult.combo_governante`, the max-As.nec row — nothing to re-derive there).

`legacy_compat` is never True here (`_con_relazione` only calls `relazione()` in standard mode), so
`_armatura_paramento_combo`'s "Fixed behaviour" branch always applies: the stem's own thrust over
its own height hs = H - sfond, not Tool 2's full-height resultants. `spinte_stelo` (the stem-only
SH.q/SH.terr) is not exposed by `ArmaturaParamentoCombo`, so it is recomputed here from the
package's own step function with the exact same arguments `tool.py` uses — the architecture brief's
allowance for an intermediate the output does not expose.

`ArmaturaParamentoResult.as_nec_cm2_m` shares its UI `symbol` hint ("A_s,nec") with the two
foundation reinforcement results (`models.py`, unrelated to this wave's `relazione`): the harness's
global highlight check matches by that exact string, so ONLY one `Passo` per report may legitimately
carry it. `relazione_armatura_fondazione.py`'s docstring names which one; this Traccia's own step
is labelled "A_s,nec (paramento)" instead, still fully explained (`nota`/`descrizione`).
"""
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura_paramento import spinte_stelo
from .models import MuroSostegnoInput, MuroSostegnoOutput
from .relazione_armatura_minima import passi_armatura_minima
from .relazione_comune import trova_spinta, trova_verifica

CLAUSE_MOMENTO = "NTC2018 §6.5.3.1.1"
CLAUSE_ARMATURA = "NTC2018 §4.1.2"


def traccia_armatura_paramento(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """6 passi: hs, SH.q (stelo), SH.terr (stelo), MEd, d, As.nec — per la combinazione governante
    del dimensionamento del paramento."""
    risultato = output.armatura_paramento
    nome = risultato.combo_governante
    spinta = trova_spinta(output, nome)
    verifica = trova_verifica(output, nome)
    combo = next(c for c in risultato.combinazioni if c.nome == nome)
    hs_m = output.geometria.h_muro_tot_m - inputs.s_fond_m
    fattore_sismico = (1 + spinta.kv) * inputs.gamma_e if spinta.sismica else 1.0
    forze_stelo = spinte_stelo(
        ka=spinta.ka, delta_d_rad=spinta.delta_d_rad, dq_kN_m2=verifica.dq_kN_m2, hs_m=hs_m,
        gamma_g_terr=spinta.gamma_g_terr, gamma_terr_kN_m3=inputs.gamma_terr_sat_kN_m3, fattore_sismico=fattore_sismico,
    )
    fyd_MPa = rebar_properties(inputs.grado_acciaio).fyd_MPa
    d_m = inputs.s_base_m - inputs.copertura_paramento_m
    return Traccia(
        titolo=f"Armatura del paramento — combinazione governante {nome}",
        passi=(
            _passo_hs(inputs, output, hs_m),
            _passo_sh_q_stelo(inputs, spinta, verifica, hs_m, forze_stelo.sh_q_kN),
            _passo_sh_terr_stelo(inputs, spinta, hs_m, forze_stelo.sh_terr_kN),
            _passo_m_ed(forze_stelo, hs_m, combo),
            _passo_d(inputs, d_m),
            _passo_as_nec(combo, fyd_MPa, d_m),
            *passi_armatura_minima(inputs, risultato, d_m=d_m, suffisso="paramento"),
        ),
    )


def _passo_hs(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, hs_m: float) -> Passo:
    return Passo(
        simbolo="hs", formula="H - s_fond",
        valori=(
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m", descrizione="altezza totale, derivata in Geometria e parametri sismici"),
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m", descrizione="spessore della fondazione"),
        ),
        risultato=hs_m, unita="m", clausola=CLAUSE_MOMENTO,
        nota="Altezza del solo fusto: la spinta sul paramento agisce solo su questa altezza, non su H.",
    )


def _passo_sh_q_stelo(inputs: MuroSostegnoInput, spinta, verifica, hs_m: float, sh_q_kN: float) -> Passo:
    termine = " * (1 + k_v) * γ_E" if spinta.sismica else ""
    valori = [
        Valore(simbolo="K_a", valore=spinta.ka, unita="-", descrizione="coefficiente di spinta attiva di questa combinazione"),
        Valore(simbolo="Dq", valore=verifica.dq_kN_m2, unita="kN/m2", descrizione="sovraccarico di progetto Dq = q·γQ"),
        Valore(simbolo="hs", valore=hs_m, unita="m", descrizione="altezza del fusto, derivata sopra"),
        Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad", descrizione="attrito terreno-muro di progetto"),
    ]
    if spinta.sismica:
        valori += [Valore(simbolo="k_v", valore=spinta.kv), Valore(simbolo="γ_E", valore=inputs.gamma_e)]
    return Passo(
        simbolo="SH_q,s", formula=f"K_a * Dq * hs * cos(δ_d){termine}",
        valori=tuple(valori), risultato=sh_q_kN, unita="kN", clausola=CLAUSE_MOMENTO,
        nota="Spinta orizzontale del sovraccarico sul solo fusto (altezza hs, non H).",
    )


def _passo_sh_terr_stelo(inputs: MuroSostegnoInput, spinta, hs_m: float, sh_terr_kN: float) -> Passo:
    termine = " * (1 + k_v) * γ_E" if spinta.sismica else ""
    valori = [
        Valore(simbolo="γ_G,terr", valore=spinta.gamma_g_terr, unita="-", descrizione="coefficiente parziale sul peso del terreno"),
        Valore(simbolo="γ_terr", valore=inputs.gamma_terr_sat_kN_m3, unita="kN/m3", descrizione="peso di volume del terreno saturo"),
        Valore(simbolo="hs", valore=hs_m, unita="m", descrizione="altezza del fusto, derivata sopra"),
        Valore(simbolo="K_a", valore=spinta.ka, unita="-"),
        Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad"),
    ]
    if spinta.sismica:
        valori += [Valore(simbolo="k_v", valore=spinta.kv), Valore(simbolo="γ_E", valore=inputs.gamma_e)]
    return Passo(
        simbolo="SH_terr,s", formula=f"0.5 * γ_G,terr * γ_terr * hs^2 * K_a * cos(δ_d){termine}",
        valori=tuple(valori), risultato=sh_terr_kN, unita="kN", clausola=CLAUSE_MOMENTO,
        nota="Spinta orizzontale del terreno sul solo fusto (altezza hs, non H).",
    )


def _passo_m_ed(forze_stelo, hs_m: float, combo) -> Passo:
    return Passo(
        simbolo="M_Ed", formula="SH_q,s * (hs / 2) + (hs / 3) * SH_terr,s",
        valori=(
            Valore(simbolo="SH_q,s", valore=forze_stelo.sh_q_kN, unita="kN", descrizione="spinta del sovraccarico sul fusto, derivata sopra"),
            Valore(simbolo="hs", valore=hs_m, unita="m", descrizione="altezza del fusto, derivata sopra (il braccio del blocco uniforme è hs/2, del cuneo triangolare hs/3)"),
            Valore(simbolo="SH_terr,s", valore=forze_stelo.sh_terr_kN, unita="kN", descrizione="spinta del terreno sul fusto, derivata sopra"),
        ),
        risultato=combo.m_ed_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento flettente di calcolo alla base del paramento.",
    )


def _passo_d(inputs: MuroSostegnoInput, d_m: float) -> Passo:
    return Passo(
        simbolo="d", formula="s_base - c_muro",
        valori=(
            Valore(simbolo="s_base", valore=inputs.s_base_m, unita="m", descrizione="spessore del muro alla base"),
            Valore(simbolo="c_muro", valore=inputs.copertura_paramento_m, unita="m", descrizione="copriferro asse barre verticali del paramento"),
        ),
        risultato=d_m, unita="m", clausola=CLAUSE_ARMATURA,
        nota="Altezza utile della sezione del paramento.",
    )


def _passo_as_nec(combo, fyd_MPa: float, d_m: float) -> Passo:
    return Passo(
        simbolo="A_s,nec (paramento)", formula="M_Ed * 10000 / (k_z * d * 1000 * f_yd)",
        valori=(
            Valore(simbolo="M_Ed", valore=combo.m_ed_kNm, unita="kNm", descrizione="momento flettente di calcolo, derivato sopra"),
            Valore(simbolo="k_z", valore=0.9, descrizione="rapporto jd/d assunto, flessione semplificata NTC2018 §4.1.2"),
            Valore(simbolo="d", valore=d_m, unita="m", descrizione="altezza utile, derivata sopra"),
            Valore(simbolo="f_yd", valore=fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio"),
        ),
        risultato=combo.as_nec_cm2_m, unita="cm2/m", clausola=CLAUSE_ARMATURA,
        nota="Area di armatura necessaria (può risultare negativa se MEd è favorevole su questa combinazione).",
    )

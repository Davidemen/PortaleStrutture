"""Verified restatement (docs/architecture-phase2.md) of `capacita_portante_fondazione.py`
(EN1997-1 Annex D strip footing, NTC2018 §6.5.3.1.1 Tab. 6.5.I / §6.4.2.1 / §7.11.5.3.1-§7.11.6.2.1
sismico), for the combination that governs the check (`CapacitaPortanteFondazioneResult.
combo_governante`, already the max-utilisation row — nothing to re-derive there). Present only when
the optional "Terreno di fondazione" block is filled (`output.capacita_portante_fondazione is not
None`, `tool.py::_esito_capacita_portante`).

`carico_limite_drenato`/`carico_limite_non_drenato` (the SAME shared function
`capacita_portante_fondazione.capacita_portante_combo` already calls) are called again here, with
the identical arguments, purely to read the intermediate factors (Nc/Nq/Nγ, iq/iγ/ic, B') that
`CapacitaPortanteCombo` does not expose — the architecture brief's allowance for reading a package's
own step functions for an unexposed intermediate. Nc/Nq/Nγ and iq/iγ/ic (EN1997-1 Annex D.4/D.2,
each itself a multi-term closed form) are cited directly, same precedent as `ca_travi.relazione_sle`
citing σ_s,limite: only the base-inclination factors bq/bc (task-mandated, `fattori_base.py`) are
restated symbolically below, since ω (the footing's own base inclination, already a muro-sostegno
input) is exactly the parameter they exist to represent. Shape factors sq=sγ=sc=1 and depth factors
dq=dc=1 always (this package always calls with `nastriforme=True` and never requests
`fattori_profondita`): both are safely omitted from the formulas below, they multiply by exactly 1.
"""
import math

from strutture.shared.capacita_portante import carico_limite_drenato, carico_limite_non_drenato
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import MuroSostegnoInput, MuroSostegnoOutput
from .relazione_comune import PI_GRECO, trova_pressioni, trova_verifica
from .ribaltamento_scorrimento import forze_normale_tangente_base

CLAUSE_ANNEX_D = "NTC2018 §6.5.3.1.1, Tab. 6.5.I, §6.4.2.1 / EN1997-1 Annex D"


def traccia_capacita_portante(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia | None:
    """8 passi: N/H alla base, B', bq, bc, q_lim, R_d, Check N_Ed/R_d<=1 — assente se il blocco
    'Terreno di fondazione' non e' compilato."""
    cp = output.capacita_portante_fondazione
    if cp is None:
        return None
    nome = cp.combo_governante
    verifica = trova_verifica(output, nome)
    pressioni = trova_pressioni(output, nome)
    combo = next(c for c in cp.combinazioni if c.nome == nome)
    omega_rad = math.radians(inputs.omega_deg)
    normale_kn, tangente_kn = forze_normale_tangente_base(n_tot_kN=verifica.n_tot_kN, r_tot_kN=verifica.r_tot_kN, omega_rad=omega_rad)
    drenata = inputs.terreno_condizione == "drenata"
    if drenata:
        risultato_limite = carico_limite_drenato(
            b_m=output.geometria.b_fond_m, l_m=output.geometria.b_fond_m, eb_m=pressioni.eccentricita_m, nastriforme=True,
            phi_deg=inputs.terreno_phi_k_deg, c_kpa=inputs.terreno_c_k_kpa, gamma_kn_m3=inputs.terreno_gamma_kn_m3,
            profondita_piano_posa_m=inputs.terreno_profondita_posa_m, profondita_falda_m=inputs.terreno_profondita_falda_m,
            h_kn=abs(tangente_kn), v_kn=normale_kn, alpha_base_deg=inputs.omega_deg,
        )
    else:
        risultato_limite = carico_limite_non_drenato(
            b_m=output.geometria.b_fond_m, l_m=output.geometria.b_fond_m, eb_m=pressioni.eccentricita_m, nastriforme=True,
            cu_kpa=inputs.terreno_cu_k_kpa, gamma_kn_m3=inputs.terreno_gamma_kn_m3,
            profondita_piano_posa_m=inputs.terreno_profondita_posa_m, h_kn=abs(tangente_kn), alpha_base_deg=inputs.omega_deg,
        )
    b_eff_m = risultato_limite.area_efficace.b_eff_m
    gamma_r = combo.q_lim_kPa * b_eff_m / combo.r_d_kN if combo.r_d_kN > 0 else float("inf")
    return Traccia(
        titolo=f"Capacità portante del terreno di fondazione (Annesso D) — combinazione governante {nome}",
        passi=(
            _passo_normale(verifica, omega_rad, normale_kn),
            _passo_tangente(verifica, omega_rad, tangente_kn),
            _passo_b_eff(output, pressioni, b_eff_m),
            *_passi_fattori_base(inputs, omega_rad, risultato_limite, drenata),
            _passo_q_lim(inputs, risultato_limite, b_eff_m, drenata),
            _passo_r_d(combo, b_eff_m, gamma_r),
            _passo_check(combo, normale_kn),
        ),
    )


def _passo_normale(verifica, omega_rad: float, normale_kn: float) -> Passo:
    return Passo(
        simbolo="N", formula="N_TOT * cos(ω) + R_TOT * sin(ω)",
        valori=(
            Valore(simbolo="N_TOT", valore=verifica.n_tot_kN, unita="kN", descrizione="risultante verticale, derivata in Ribaltamento e scorrimento"),
            Valore(simbolo="ω", valore=omega_rad, unita="rad", descrizione="inclinazione della base di fondazione"),
            Valore(simbolo="R_TOT", valore=verifica.r_tot_kN, unita="kN", descrizione="risultante orizzontale, derivata in Ribaltamento e scorrimento"),
        ),
        risultato=normale_kn, unita="kN", clausola="EN1997-1 Annex D.2 nota 2",
        nota="Componente normale alla base (inclinata di ω) delle risultanti Ntot/Rtot.",
    )


def _passo_tangente(verifica, omega_rad: float, tangente_kn: float) -> Passo:
    return Passo(
        simbolo="H_base", formula="abs(R_TOT * cos(ω) - N_TOT * sin(ω))",
        valori=(
            Valore(simbolo="R_TOT", valore=verifica.r_tot_kN, unita="kN"),
            Valore(simbolo="ω", valore=omega_rad, unita="rad"),
            Valore(simbolo="N_TOT", valore=verifica.n_tot_kN, unita="kN"),
        ),
        risultato=abs(tangente_kn), unita="kN", clausola="EN1997-1 Annex D.2 nota 2",
        nota="Componente tangenziale alla base (inclinata di ω) delle risultanti Ntot/Rtot.",
    )


def _passo_b_eff(output: MuroSostegnoOutput, pressioni, b_eff_m: float) -> Passo:
    return Passo(
        simbolo="B'", formula="B - 2 * abs(e)",
        valori=(
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="e", valore=pressioni.eccentricita_m, unita="m", descrizione="eccentricità della risultante, derivata in Pressioni sul terreno di fondazione"),
        ),
        risultato=b_eff_m, unita="m", clausola="EN1997-1 Annex D.1",
        nota="Larghezza efficace di Meyerhof (base nastriforme, per metro di sviluppo).",
    )


def _passi_fattori_base(inputs: MuroSostegnoInput, omega_rad: float, risultato_limite, drenata: bool) -> tuple[Passo, ...]:
    base = risultato_limite.fattori_inclinazione_base
    if drenata:
        phi_valore = Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°", descrizione="angolo di attrito interno caratteristico del terreno di fondazione — coefficiente parziale unitario anche nelle combinazioni sismiche (NTC2018 §7.11.1, registro: muro-sostegno/capacita-portante-sismica-parametri-caratteristici)")
        passo_bq = Passo(
            simbolo="b_q", formula="(1 - abs(ω) * tan(φ'_k))^2",
            valori=(Valore(simbolo="ω", valore=omega_rad, unita="rad", descrizione="inclinazione della base di fondazione"), phi_valore),
            risultato=base.bq, unita="-", clausola="EN1997-1 Annex D.2",
            nota="Fattore di inclinazione della base sui termini Nq/Nγ (bγ = bq).",
        )
        passo_bc = Passo(
            simbolo="b_c", formula="b_q - (1 - b_q) / (N_c * tan(φ'_k))",
            valori=(
                Valore(simbolo="b_q", valore=base.bq, descrizione="fattore di inclinazione della base, derivato sopra"),
                Valore(simbolo="N_c", valore=risultato_limite.fattori_portanza.nc, descrizione="fattore di capacità portante Nc, EN1997-1 Annex D.4, funzione di φ'_k"),
                phi_valore,
            ),
            risultato=base.bc, unita="-", clausola="EN1997-1 Annex D.2",
            nota="Fattore di inclinazione della base sul termine di coesione Nc.",
        )
        return (passo_bq, passo_bc)
    passo_bc = Passo(
        simbolo="b_c", formula="1 - 2 * abs(ω) / (π + 2)",
        valori=(
            Valore(simbolo="ω", valore=omega_rad, unita="rad", descrizione="inclinazione della base di fondazione"),
            Valore(simbolo="π", valore=PI_GRECO),
        ),
        risultato=base.bc, unita="-", clausola="EN1997-1 Annex D.3",
        nota="Fattore di inclinazione della base, condizione non drenata (bq=bγ=1, non usati dalla formula non drenata).",
    )
    return (passo_bc,)


def _passo_q_lim(inputs: MuroSostegnoInput, risultato_limite, b_eff_m: float, drenata: bool) -> Passo:
    base = risultato_limite.fattori_inclinazione_base
    ic = risultato_limite.fattori_inclinazione_carico
    if drenata:
        portanza = risultato_limite.fattori_portanza
        return Passo(
            simbolo="q_lim", formula="c'_k * N_c * b_c * i_c + q' * N_q * b_q * i_q + 0.5 * γ'_eff * B' * N_γ * b_γ * i_γ",
            valori=(
                Valore(simbolo="c'_k", valore=inputs.terreno_c_k_kpa, unita="kPa", descrizione="coesione efficace caratteristica del terreno di fondazione"),
                Valore(simbolo="N_c", valore=risultato_limite.fattori_portanza.nc, descrizione="fattore di capacità portante Nc, EN1997-1 Annex D.4"),
                Valore(simbolo="b_c", valore=base.bc, descrizione="fattore di inclinazione della base, derivato sopra"),
                Valore(simbolo="i_c", valore=ic.ic, descrizione="fattore di inclinazione del carico ic, EN1997-1 Annex D.2, funzione di H/V"),
                Valore(simbolo="q'", valore=risultato_limite.q_eff_kpa, unita="kPa", descrizione="sovraccarico efficace al piano di posa (tiene conto della falda, se presente)"),
                Valore(simbolo="N_q", valore=portanza.nq, descrizione="fattore di capacità portante Nq, EN1997-1 Annex D.4"),
                Valore(simbolo="b_q", valore=base.bq, descrizione="fattore di inclinazione della base, derivato sopra"),
                Valore(simbolo="i_q", valore=ic.iq, descrizione="fattore di inclinazione del carico iq, EN1997-1 Annex D.2"),
                Valore(simbolo="γ'_eff", valore=risultato_limite.gamma_eff_kn_m3, unita="kN/m3", descrizione="peso di volume efficace (tiene conto della falda, se presente)"),
                Valore(simbolo="B'", valore=b_eff_m, unita="m", descrizione="larghezza efficace, derivata sopra"),
                Valore(simbolo="N_γ", valore=portanza.ngamma, descrizione="fattore di capacità portante Nγ, EN1997-1 Annex D.4"),
                Valore(simbolo="b_γ", valore=base.bgamma, descrizione="fattore di inclinazione della base (= b_q, EN1997-1 Annex D.2)"),
                Valore(simbolo="i_γ", valore=ic.igamma, descrizione="fattore di inclinazione del carico iγ, EN1997-1 Annex D.2"),
            ),
            risultato=risultato_limite.q_lim_kpa, unita="kPa", clausola=CLAUSE_ANNEX_D,
            nota="Pressione limite di capacità portante, condizione drenata (forma/profondità = 1, base nastriforme senza fattori di profondità).",
        )
    return Passo(
        simbolo="q_lim", formula="(π + 2) * c_u,k * b_c * i_c + q",
        valori=(
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="c_u,k", valore=inputs.terreno_cu_k_kpa, unita="kPa", descrizione="resistenza al taglio non drenata caratteristica del terreno di fondazione"),
            Valore(simbolo="b_c", valore=base.bc, descrizione="fattore di inclinazione della base, derivato sopra"),
            Valore(simbolo="i_c", valore=ic.ic, descrizione="fattore di inclinazione del carico ic, EN1997-1 Annex D.3, funzione di H"),
            Valore(simbolo="q", valore=risultato_limite.q_eff_kpa, unita="kPa", descrizione="sovraccarico totale al piano di posa"),
        ),
        risultato=risultato_limite.q_lim_kpa, unita="kPa", clausola=CLAUSE_ANNEX_D,
        nota="Pressione limite di capacità portante, condizione non drenata.",
    )


def _passo_r_d(combo, b_eff_m: float, gamma_r: float) -> Passo:
    return Passo(
        simbolo="R_d", formula="q_lim * B' / γ_R",
        valori=(
            Valore(simbolo="q_lim", valore=combo.q_lim_kPa, unita="kPa", descrizione="pressione limite, derivata sopra"),
            Valore(simbolo="B'", valore=b_eff_m, unita="m", descrizione="larghezza efficace (= area efficace per metro di sviluppo, base nastriforme)"),
            Valore(simbolo="γ_R", valore=gamma_r, descrizione="coefficiente parziale di resistenza, NTC2018 Tab. 6.5.I: 1.4 statico (R3, Approccio 2) / 1.2 sismico (§7.11.6.2.1)"),
        ),
        risultato=combo.r_d_kN, unita="kN", clausola=CLAUSE_ANNEX_D,
        nota="Resistenza di progetto, per metro di sviluppo del muro.",
    )


def _passo_check(combo, normale_kn: float) -> Passo:
    soddisfatta = combo.rapporto <= 1.0
    return Passo(
        simbolo="N_Ed/R_d", formula="N_Ed / R_d <= 1",
        valori=(
            Valore(simbolo="N_Ed", valore=normale_kn, unita="kN", descrizione="azione normale di progetto alla base, derivata sopra"),
            Valore(simbolo="R_d", valore=combo.r_d_kN, unita="kN", descrizione="resistenza di progetto, derivata sopra"),
        ),
        risultato=combo.rapporto, unita="-", clausola=CLAUSE_ANNEX_D,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Grado di sfruttamento del terreno di fondazione.",
    )

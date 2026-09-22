"""Verified restatement (docs/architecture-phase2.md) of `ribaltamento_scorrimento.py`: overturning
and sliding safety factors of a gravity retaining wall, both NTC2018 §6.5.3.1.1 Tab. 6.5.I / EC7
§6.5.4 (review finding WRONG_CLAUSE: overturning used to cite §6.5.3.1.2, the EMBEDDED-WALL
("paratie") sub-clause — `ribaltamento_scorrimento.py:12`'s own constant already names §6.5.3.1.1
for `GAMMA_R_RIBALTAMENTO_R3`), γR included. The GOVERNING combination
(`relazione_comune.combo_governante_stabilita`) gets the full symbolic derivation, reusing the
thrust/weights of `relazione_spinta.py` (docs/architecture-phase2.md §5); the other 7 restate the
SAME two formulas with their own numbers straight from the output (a many-rows tool "traces the
governing row only" — the formula, shown once in full, still applies identically to every row, so
every `Check` still gets its own `Passo`, docs/architecture-phase2.md §4/§6). γR is read off
`Check.limit` (already the exact threshold `tool.py::soglia_verifica` picked for that row — statico
Tab. 6.5.I R3, sismico γR=1 §7.11.6.2.1), never re-derived.
"""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .combinazioni import ALL_COMBOS
from .models import MuroSostegnoInput, MuroSostegnoOutput, NomeCombo
from .relazione_comune import combo_governante_stabilita, nome_combo_leggibile, trova_spinta, trova_verifica

CLAUSE_RIBALTAMENTO = "NTC2018 §6.5.3.1.1"  # review finding WRONG_CLAUSE: era §6.5.3.1.2 (paratie)
CLAUSE_SCORRIMENTO = "NTC2018 §6.5.3.1.1 / EC7 §6.5.4"
CLAUSE_INERZIA_SISMICA = "EN1998-5 §7.3.2.2(2)P"
_ESITO = {True: "soddisfatta", False: "non soddisfatta"}


def traccia_stabilita(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """20 passi (22 quando la combinazione governante è sismica: +F_h, +M_fh — review finding
    MISSING_STEP): derivazione completa di [F_h, M_fh,] MRIB/MSTAB/OR/NTOT/RTOT/OS per la
    combinazione governante, più un passo OR e un passo OS per ciascuna delle altre 7 combinazioni
    (16 Check in totale, uno per ciascun ribaltamento/scorrimento)."""
    nome_gov = combo_governante_stabilita(output)
    spinta_gov = trova_spinta(output, nome_gov)
    omega_rad = math.radians(inputs.omega_deg)
    passi = ()
    if spinta_gov.sismica:
        passi = (_passo_fh(output, nome_gov), _passo_mfh(output, nome_gov))
    passi = (
        *passi,
        _passo_m_rib(output, nome_gov), _passo_m_stab(output, nome_gov), _passo_or(output, nome_gov),
        _passo_n_tot(output, nome_gov), _passo_r_tot(output, nome_gov),
        *_passi_phi_base(inputs, output, nome_gov), _passo_os(output, nome_gov, omega_rad),
    )
    for nome in ALL_COMBOS:
        if nome == nome_gov:
            continue
        passi = (*passi, _passo_or_riepilogo(output, nome), _passo_os_riepilogo(output, nome, omega_rad))
    return Traccia(
        titolo=f"Ribaltamento e scorrimento — combinazione governante {nome_combo_leggibile(nome_gov)}",
        passi=passi,
    )


def _passo_fh(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    """Review finding (MISSING_STEP): F_h (inerzia sismica orizzontale del muro+terreno,
    EN1998-5 §7.3.2.2(2)P — ~12% di R_TOT nell'esempio) entrava in R_TOT come numero nudo, senza
    alcun passo che lo derivasse."""
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    assert spinta.kh is not None
    return Passo(
        simbolo="F_h", formula="k_h * (W_muro + W_terr)",
        valori=(
            Valore(simbolo="k_h", valore=spinta.kh, descrizione="coefficiente sismico orizzontale, derivato in Geometria e parametri sismici"),
            Valore(simbolo="W_muro", valore=spinta.w_muro_kN, unita="kN", descrizione="peso proprio del muro, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato in Spinta attiva e pesi stabilizzanti"),
        ),
        risultato=verifica.fh_kN, unita="kN", clausola=CLAUSE_INERZIA_SISMICA,
        nota="Forza d'inerzia orizzontale del muro e del terreno (analisi pseudostatica).",
    )


def _passo_mfh(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    """Review finding (MISSING_STEP): stesso difetto di F_h, per M_fh (~11% di M_RIB nell'esempio)."""
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    geometria = output.geometria
    assert spinta.kh is not None
    return Passo(
        simbolo="M_fh", formula="k_h * (W_muro * z_muro + W_terr * z_terr)",
        valori=(
            Valore(simbolo="k_h", valore=spinta.kh, descrizione="coefficiente sismico orizzontale, derivato in Geometria e parametri sismici"),
            Valore(simbolo="W_muro", valore=spinta.w_muro_kN, unita="kN", descrizione="peso proprio del muro, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="z_muro", valore=geometria.z_muro_m, unita="m", descrizione="baricentro del muro dalla base della fondazione (composito, non ristato)"),
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="z_terr", valore=geometria.z_terr_m, unita="m", descrizione="baricentro del terreno, derivato in Geometria e parametri sismici"),
        ),
        risultato=verifica.m_fh_kNm, unita="kNm", clausola=CLAUSE_INERZIA_SISMICA,
        nota="Momento ribaltante della forza d'inerzia orizzontale del muro e del terreno.",
    )


def _passo_m_rib(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    if spinta.sismica:
        simbolo = "M_RIB (sismica, braccio H/2)"
        formula = "SH_q * H / 2 + SH_terr * (H / 2) + M_fh"
        valori = (
            Valore(simbolo="SH_q", valore=verifica.sh_q_kN, unita="kN", descrizione="spinta orizzontale del sovraccarico, derivata sopra"),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m", descrizione="altezza totale, derivata sopra"),
            Valore(simbolo="SH_terr", valore=verifica.sh_terr_kN, unita="kN", descrizione="spinta orizzontale del terreno, derivata sopra"),
            Valore(simbolo="M_fh", valore=verifica.m_fh_kNm, unita="kNm", descrizione="momento della forza d'inerzia orizzontale del muro+terreno, derivato sopra"),
        )
        nota = "Momento ribaltante: braccio H/2 nelle combinazioni sismiche, più il momento dell'inerzia orizzontale del monolite."
    else:
        # Review finding (MISLEADING): il simbolo dichiara il braccio H/3 usato SOLO da questa riga
        # statica — le righe di riepilogo delle altre 7 combinazioni (sotto) riusano lo stesso
        # simbolo bare "M_RIB"/"M_STAB" come Valore citato, ciascuna con il braccio effettivamente
        # usato per la propria natura statica/sismica (mai esposto in un altro passo di questa
        # Traccia): un lettore non può più confondere il braccio H/2 di questa riga (se governasse
        # una combinazione sismica) con l'H/3 usato qui.
        simbolo = "M_RIB (statica, braccio H/3)"
        formula = "SH_q * H / 2 + SH_terr * (H / 3)"
        valori = (
            Valore(simbolo="SH_q", valore=verifica.sh_q_kN, unita="kN", descrizione="spinta orizzontale del sovraccarico, derivata sopra"),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m", descrizione="altezza totale, derivata sopra"),
            Valore(simbolo="SH_terr", valore=verifica.sh_terr_kN, unita="kN", descrizione="spinta orizzontale del terreno, derivata sopra"),
        )
        nota = "Momento ribaltante: braccio H/3 nelle combinazioni statiche (diagramma triangolare)."
    return Passo(
        simbolo=simbolo, formula=formula, valori=valori, risultato=verifica.m_rib_kNm, unita="kNm",
        clausola=CLAUSE_RIBALTAMENTO, nota=nota,
    )


def _passo_m_stab(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    return Passo(
        simbolo="M_STAB", formula="(SV_q + SV_terr) * x_sv + M_terr + M_muro",
        valori=(
            Valore(simbolo="SV_q", valore=verifica.sv_q_kN, unita="kN", descrizione="spinta verticale del sovraccarico, derivata sopra"),
            Valore(simbolo="SV_terr", valore=verifica.sv_terr_kN, unita="kN", descrizione="spinta verticale del terreno, derivata sopra"),
            Valore(simbolo="x_sv", valore=output.geometria.x_sv_m, unita="m", descrizione="braccio della spinta verticale (coincide con x_terr per definizione geometrica)"),
            Valore(simbolo="M_terr", valore=spinta.m_terr_kNm, unita="kNm", descrizione="momento stabilizzante del terreno, derivato sopra"),
            Valore(simbolo="M_muro", valore=spinta.m_muro_kNm, unita="kNm", descrizione="momento stabilizzante del muro, derivato sopra"),
        ),
        risultato=verifica.m_stab_kNm, unita="kNm", clausola=CLAUSE_RIBALTAMENTO,
        nota="Momento stabilizzante rispetto alla punta di valle.",
    )


def _passo_or(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    verifica = trova_verifica(output, nome)
    return Passo(
        simbolo="OR", formula="M_STAB / M_RIB >= γ_R",
        valori=(
            Valore(simbolo="M_STAB", valore=verifica.m_stab_kNm, unita="kNm", descrizione="momento stabilizzante, derivato sopra"),
            Valore(simbolo="M_RIB", valore=verifica.m_rib_kNm, unita="kNm", descrizione="momento ribaltante, derivato sopra"),
            Valore(simbolo="γ_R", valore=verifica.verifica_ribaltamento.limit, descrizione="coefficiente parziale di resistenza, NTC2018 Tab. 6.5.I R3 (statico) / γR=1 (sismico, §7.11.6.2.1)"),
        ),
        risultato=verifica.or_ribaltamento, unita="-", clausola=CLAUSE_RIBALTAMENTO,
        esito=_ESITO[verifica.verifica_ribaltamento.passed],
        nota="Fattore di sicurezza a ribaltamento, momento stabilizzante su momento ribaltante.",
    )


def _passo_n_tot(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    return Passo(
        simbolo="N_TOT", formula="W_muro + W_terr + SV_q + SV_terr",
        valori=(
            Valore(simbolo="W_muro", valore=spinta.w_muro_kN, unita="kN", descrizione="peso proprio del muro, derivato sopra"),
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato sopra"),
            Valore(simbolo="SV_q", valore=verifica.sv_q_kN, unita="kN", descrizione="spinta verticale del sovraccarico, derivata sopra"),
            Valore(simbolo="SV_terr", valore=verifica.sv_terr_kN, unita="kN", descrizione="spinta verticale del terreno, derivata sopra"),
        ),
        risultato=verifica.n_tot_kN, unita="kN", clausola=CLAUSE_SCORRIMENTO,
        nota="Risultante verticale totale alla base della fondazione.",
    )


def _passo_r_tot(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    if spinta.sismica:
        formula = "SH_q + SH_terr + F_h"
        valori = (
            Valore(simbolo="SH_q", valore=verifica.sh_q_kN, unita="kN"),
            Valore(simbolo="SH_terr", valore=verifica.sh_terr_kN, unita="kN"),
            Valore(simbolo="F_h", valore=verifica.fh_kN, unita="kN", descrizione="forza d'inerzia orizzontale del muro+terreno, EN1998-5 §7.3.2.2(2)P, kh·(Wmuro+Wterr)"),
        )
    else:
        formula = "SH_q + SH_terr"
        valori = (Valore(simbolo="SH_q", valore=verifica.sh_q_kN, unita="kN"), Valore(simbolo="SH_terr", valore=verifica.sh_terr_kN, unita="kN"))
    return Passo(
        simbolo="R_TOT", formula=formula, valori=valori, risultato=verifica.r_tot_kN, unita="kN",
        clausola=CLAUSE_SCORRIMENTO, nota="Risultante orizzontale totale alla base della fondazione.",
    )


def _passo_os(output: MuroSostegnoOutput, nome: NomeCombo, omega_rad: float) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    return Passo(
        simbolo="OS", formula="tan(φ_d,base) * (N_TOT * cos(ω) + R_TOT * sin(ω)) / (R_TOT * cos(ω) - N_TOT * sin(ω)) >= γ_R",
        valori=(
            Valore(simbolo="φ_d,base", valore=verifica.phi_scorrimento_rad, unita="rad", descrizione=_descrizione_phi_base(spinta, verifica)),
            Valore(simbolo="N_TOT", valore=verifica.n_tot_kN, unita="kN", descrizione="risultante verticale, derivata sopra"),
            Valore(simbolo="R_TOT", valore=verifica.r_tot_kN, unita="kN", descrizione="risultante orizzontale, derivata sopra"),
            Valore(simbolo="ω", valore=omega_rad, unita="rad", descrizione="inclinazione della base di fondazione"),
            Valore(simbolo="γ_R", valore=verifica.verifica_scorrimento.limit, descrizione="coefficiente parziale di resistenza, NTC2018 Tab. 6.5.I R3 (statico) / γR=1 (sismico, §7.11.6.2.1)"),
        ),
        risultato=verifica.os_scorrimento, unita="-", clausola=CLAUSE_SCORRIMENTO,
        esito=_ESITO[verifica.verifica_scorrimento.passed],
        nota="Fattore di sicurezza a scorrimento: componenti normale/tangenziale di Ntot/Rtot sulla base (inclinata di ω).",
    )


def _passo_or_riepilogo(output: MuroSostegnoOutput, nome: NomeCombo) -> Passo:
    verifica = trova_verifica(output, nome)
    return Passo(
        simbolo=f"OR ({nome_combo_leggibile(nome)})", formula="M_STAB / M_RIB >= γ_R",
        valori=(
            Valore(simbolo="M_STAB", valore=verifica.m_stab_kNm, unita="kNm", descrizione="momento stabilizzante di questa combinazione, stessa formula sopra"),
            Valore(simbolo="M_RIB", valore=verifica.m_rib_kNm, unita="kNm", descrizione="momento ribaltante di questa combinazione, stessa formula sopra"),
            Valore(simbolo="γ_R", valore=verifica.verifica_ribaltamento.limit),
        ),
        risultato=verifica.or_ribaltamento, unita="-", clausola=CLAUSE_RIBALTAMENTO,
        esito=_ESITO[verifica.verifica_ribaltamento.passed],
    )


def _passo_os_riepilogo(output: MuroSostegnoOutput, nome: NomeCombo, omega_rad: float) -> Passo:
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    return Passo(
        simbolo=f"OS ({nome_combo_leggibile(nome)})",
        formula="tan(φ_d,base) * (N_TOT * cos(ω) + R_TOT * sin(ω)) / (R_TOT * cos(ω) - N_TOT * sin(ω)) >= γ_R",
        valori=(
            Valore(simbolo="φ_d,base", valore=verifica.phi_scorrimento_rad, unita="rad", descrizione=_descrizione_phi_base(spinta, verifica)),
            Valore(simbolo="N_TOT", valore=verifica.n_tot_kN, unita="kN"),
            Valore(simbolo="R_TOT", valore=verifica.r_tot_kN, unita="kN"),
            Valore(simbolo="ω", valore=omega_rad, unita="rad", descrizione="inclinazione della base di fondazione (comune a tutte le combinazioni)"),
            Valore(simbolo="γ_R", valore=verifica.verifica_scorrimento.limit),
        ),
        risultato=verifica.os_scorrimento, unita="-", clausola=CLAUSE_SCORRIMENTO,
        esito=_ESITO[verifica.verifica_scorrimento.passed],
    )


def _usa_terreno_di_fondazione(spinta, verifica) -> bool:
    return abs(verifica.phi_scorrimento_rad - spinta.phi_d_rad) > 1e-12


def _descrizione_phi_base(spinta, verifica) -> str:
    if _usa_terreno_di_fondazione(spinta, verifica):
        return "attrito di progetto del terreno di fondazione sul piano di posa (blocco 'Terreno di fondazione', derivato sopra)"
    return "attrito di progetto del rinterro, derivato sopra: senza un terreno di fondazione distinto è l'unico noto"


def _passi_phi_base(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, nome: NomeCombo) -> tuple[Passo, ...]:
    """φ_d,base = atan(tan(φ'_k,fond)/γ_φ) when the sliding check uses the foundation soil."""
    spinta, verifica = trova_spinta(output, nome), trova_verifica(output, nome)
    if not _usa_terreno_di_fondazione(spinta, verifica):
        return ()
    return (Passo(
        simbolo="φ_d,base", formula="atan(tan(φ'_k,fond) / γ_φ)",
        valori=(
            Valore(simbolo="φ'_k,fond", valore=inputs.terreno_phi_k_deg, unita="°", descrizione="angolo di attrito caratteristico del terreno di fondazione"),
            Valore(simbolo="γ_φ", valore=spinta.gamma_phi_terr, descrizione="coefficiente parziale su tan φ' di questa combinazione, NTC2018 Tab. 6.2.II"),
        ),
        risultato=verifica.phi_scorrimento_rad, unita="rad", clausola="NTC2018 §6.5.3.1.1 / EN 1997-1 §6.5.3",
        nota="Resistenza allo scorrimento sul piano di posa: terreno di fondazione, non rinterro (registro: muro-sostegno/scorrimento-con-attrito-del-terreno-di-fondazione).",
    ),)

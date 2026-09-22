"""Verified restatement (docs/architecture-phase2.md) of `angoli_progetto.py` (φd/δd, NTC2018 Tab.
6.2.II), `coulomb.py`/`mononobe_okabe.py` (active thrust coefficient Ka, Coulomb static / Mononobe-
Okabe seismic, both via the shared `rapporto_spinta.py` U/(V·(1+√(W/X))²) form — NTC2018
§6.5.3.1.1 / §7.11.6.2.1) and `ribaltamento_scorrimento.spinte_orizzontali_verticali`/`pesi.py`
(thrust components and stabilising weights) — for the ONE combination that governs BOTH
ribaltamento and scorrimento (docs/architecture-phase2.md §5, "trace the governing row only";
`relazione_comune.combo_governante_stabilita`).

β/ψ are converted to radians once (plain unit conversion, no formula of its own) so every trig call
below operates on already-radian values (φd/δd/θ are radians already): mixing a `°`-tagged bare
identifier into a compound trig argument would silently skip the notation grammar's degree-aware
evaluation (`valuta.py` only converts a BARE identifier argument, never a sum) — every trig
argument here is therefore deliberately a sum/difference, never a lone `°` identifier.

The wall's own composite area/centroid (A_muro/x_muro, `GeometriaResult`) is cited directly, not
re-derived (see `relazione_geometria.py`'s docstring); the backfill's (A_terr/x_terr) was already
derived there and is cited here without repeating the formula. `legacy_compat` is never True here
(`_con_relazione` only calls `relazione()` in standard mode, see `strutture.shared.tool`), so the
seismic-inertia terms (kv_factor on the weights, γE on the thrust) always apply on a seismic row.
"""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .models import MuroSostegnoInput, MuroSostegnoOutput, SpintaCombo
from .relazione_comune import combo_governante_stabilita, nome_combo_leggibile, trova_spinta, trova_verifica


def traccia_spinta(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """11 passi (13 quando la combinazione governante è sismica): [k_v, θ], φd, δd, Ka, SH.terr,
    SV.terr, SH.q, SV.q, Wmuro, Mmuro, Wterr, Mterr — per la combinazione che governa
    ribaltamento/scorrimento.

    Review finding (MISSING_STEP): `relazione_geometria.py` deriva k_v/θ SOLO per SISMA_1
    (segno_kv=+1, vedi il suo stesso docstring); quando la combinazione governante è SISMA_2
    (segno_kv=-1, come nell'esempio) il passo K_a sostituiva un θ diverso (segno incluso) descritto
    come "derivato in Geometria e parametri sismici" — falso per quel segno. k_v/θ sono ora
    derivati QUI, per la combinazione governante, segno esplicito fra i Valori."""
    nome = combo_governante_stabilita(output)
    spinta = trova_spinta(output, nome)
    beta_rad, psi_rad = math.radians(inputs.beta_deg), math.radians(inputs.psi_deg)
    passi = (_passo_phi_d(inputs, spinta), _passo_delta_d(inputs, spinta))
    if spinta.sismica:
        passi = (*passi, _passo_kv_combinazione(spinta), _passo_theta_combinazione(spinta))
    passi = (
        *passi,
        _passo_ka(inputs, spinta, beta_rad, psi_rad),
        _passo_sh_terr(inputs, output, spinta), _passo_sv_terr(inputs, output, spinta),
        _passo_sh_q(inputs, output, spinta), _passo_sv_q(inputs, output, spinta),
        _passo_w_muro(inputs, output, spinta), _passo_m_muro(output, spinta),
        _passo_w_terr(inputs, output, spinta), _passo_m_terr(output, spinta),
    )
    return Traccia(
        titolo=f"Spinta attiva e pesi stabilizzanti — combinazione governante {nome_combo_leggibile(nome)}",
        passi=passi,
    )


def _passo_kv_combinazione(spinta: SpintaCombo) -> Passo:
    assert spinta.kh is not None and spinta.kv is not None
    segno = 1.0 if spinta.nome == "SISMA_1" else -1.0
    return Passo(
        simbolo="k_v", formula="segno_kv * 0.5 * k_h",
        valori=(
            Valore(simbolo="segno_kv", valore=segno, descrizione="+1 per SISMA_1, −1 per SISMA_2 (EN1998-5 §7.3.2.2(2)P)"),
            Valore(simbolo="k_h", valore=spinta.kh, descrizione="coefficiente sismico orizzontale, derivato in Geometria e parametri sismici (uguale per SISMA_1 e SISMA_2)"),
        ),
        risultato=spinta.kv, unita="-", clausola="NTC2018 §7.11.6.2.1",
        nota=f"Coefficiente sismico verticale per {spinta.nome}, segno incluso.",
    )


def _passo_theta_combinazione(spinta: SpintaCombo) -> Passo:
    assert spinta.kh is not None and spinta.kv is not None and spinta.theta_rad is not None
    return Passo(
        simbolo="θ", formula="atan(k_h / (1 + k_v))",
        valori=(
            Valore(simbolo="k_h", valore=spinta.kh, descrizione="coefficiente sismico orizzontale, derivato in Geometria e parametri sismici"),
            Valore(simbolo="k_v", valore=spinta.kv, descrizione="coefficiente sismico verticale per questa combinazione, derivato sopra"),
        ),
        risultato=spinta.theta_rad, unita="rad", clausola="NTC2018 §7.11.6.2.1",
        nota=f"Angolo che entra nel coefficiente di spinta attiva sismica di Mononobe-Okabe, per {spinta.nome}.",
    )


def _passo_phi_d(inputs: MuroSostegnoInput, spinta: SpintaCombo) -> Passo:
    return Passo(
        simbolo="φ_d", formula="atan(tan(φ) / γ_φ,terr)",
        valori=(
            Valore(simbolo="φ", valore=inputs.phi_deg, unita="°", descrizione="angolo di attrito interno del terreno"),
            Valore(simbolo="γ_φ,terr", valore=spinta.gamma_phi_terr, descrizione="coefficiente parziale sull'angolo di attrito del terreno, NTC2018 Tab. 6.2.II"),
        ),
        risultato=spinta.phi_d_rad, unita="rad", clausola="NTC2018 Tab. 6.2.II",
        nota="Angolo di attrito interno di progetto del terreno.",
    )


def _passo_delta_d(inputs: MuroSostegnoInput, spinta: SpintaCombo) -> Passo:
    return Passo(
        simbolo="δ_d", formula="atan(tan(δ) / γ_φ,terr)",
        valori=(
            Valore(simbolo="δ", valore=inputs.delta_deg, unita="°", descrizione="angolo di attrito terreno-muro"),
            Valore(simbolo="γ_φ,terr", valore=spinta.gamma_phi_terr, descrizione="stesso coefficiente di φ_d sopra"),
        ),
        risultato=spinta.delta_d_rad, unita="rad", clausola="NTC2018 Tab. 6.2.II",
        nota="Angolo di attrito terreno-muro di progetto.",
    )


def _passo_ka(inputs: MuroSostegnoInput, spinta: SpintaCombo, beta_rad: float, psi_rad: float) -> Passo:
    valori = [
        Valore(simbolo="ψ", valore=psi_rad, unita="rad", descrizione=f"inclinazione del paramento interno, {inputs.psi_deg:g}°"),
        Valore(simbolo="φ_d", valore=spinta.phi_d_rad, unita="rad", descrizione="angolo di attrito di progetto, derivato sopra"),
        Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad", descrizione="attrito terreno-muro di progetto, derivato sopra"),
    ]
    if spinta.sismica:
        valori.append(Valore(simbolo="θ", valore=spinta.theta_rad, unita="rad", descrizione="angolo sismico, derivato sopra"))
        cuneo_valido = beta_rad <= (spinta.phi_d_rad - spinta.theta_rad)
        numeratore = "sin(ψ + φ_d - θ)^2"
        denominatore_base = "cos(θ) * sin(ψ)^2 * sin(ψ - δ_d - θ)"
        w = "sin(φ_d + δ_d) * sin(φ_d - β - θ)"
        x = "sin(ψ - δ_d - θ) * sin(ψ + β)"
        clausola = "NTC2018 §7.11.6.2.1 / EC8-5 Annex E"
        nota = "Coefficiente di spinta attiva sismica (Mononobe-Okabe), combinazione sismica."
    else:
        cuneo_valido = beta_rad <= spinta.phi_d_rad
        numeratore = "sin(ψ + φ_d)^2"
        denominatore_base = "sin(ψ)^2 * sin(ψ - δ_d)"
        w = "sin(φ_d + δ_d) * sin(φ_d - β)"
        x = "sin(ψ - δ_d) * sin(ψ + β)"
        clausola = "NTC2018 §6.5.3.1.1"
        nota = "Coefficiente di spinta attiva (Coulomb), combinazione statica."
    if cuneo_valido:
        valori.append(Valore(simbolo="β", valore=beta_rad, unita="rad", descrizione=f"inclinazione del pendio a tergo, {inputs.beta_deg:g}°"))
        formula = f"{numeratore} / ({denominatore_base} * (1 + sqrt(({w}) / ({x})))^2)"
    else:
        formula = f"{numeratore} / ({denominatore_base})"
        nota += " Cuneo di spinta non ammissibile (β > φ_d): termine correttivo escluso."
    return Passo(simbolo="K_a", formula=formula, valori=tuple(valori), risultato=spinta.ka, unita="-", clausola=clausola, nota=nota)


def _termine_sismico(spinta: SpintaCombo, *, con_gamma_e: bool) -> str:
    if not spinta.sismica:
        return ""
    return " * (1 + k_v) * γ_E" if con_gamma_e else " * (1 + k_v)"


def _valori_kv_gamma_e(inputs: MuroSostegnoInput, spinta: SpintaCombo) -> tuple[Valore, ...]:
    if not spinta.sismica:
        return ()
    return (
        Valore(simbolo="k_v", valore=spinta.kv, descrizione="coefficiente sismico verticale di questa combinazione, derivato sopra"),
        Valore(simbolo="γ_E", valore=inputs.gamma_e, descrizione="fattore moltiplicativo sulla spinta sismica"),
    )


def _passo_sh_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=True)
    verifica = trova_verifica(output, spinta.nome)
    return Passo(
        simbolo="SH_terr", formula=f"0.5 * γ_G,terr * γ_terr * H^2 * K_a * cos(δ_d){termine}",
        valori=(
            Valore(simbolo="γ_G,terr", valore=spinta.gamma_g_terr, descrizione="coefficiente parziale sul peso del terreno"),
            Valore(simbolo="γ_terr", valore=inputs.gamma_terr_sat_kN_m3, unita="kN/m3", descrizione="peso di volume del terreno saturo"),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m", descrizione="altezza totale, derivata in Geometria e parametri sismici"),
            Valore(simbolo="K_a", valore=spinta.ka, descrizione="coefficiente di spinta attiva, derivato sopra"),
            Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad", descrizione="attrito terreno-muro di progetto, derivato sopra"),
            *_valori_kv_gamma_e(inputs, spinta),
        ),
        risultato=verifica.sh_terr_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Componente orizzontale della spinta del terreno.",
    )


def _passo_sv_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=True)
    verifica = trova_verifica(output, spinta.nome)
    return Passo(
        simbolo="SV_terr", formula=f"0.5 * γ_G,terr * γ_terr * H^2 * K_a * sin(δ_d){termine}",
        valori=(
            Valore(simbolo="γ_G,terr", valore=spinta.gamma_g_terr, descrizione="coefficiente parziale sul peso del terreno"),
            Valore(simbolo="γ_terr", valore=inputs.gamma_terr_sat_kN_m3, unita="kN/m3"),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m"),
            Valore(simbolo="K_a", valore=spinta.ka),
            Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad"),
            *_valori_kv_gamma_e(inputs, spinta),
        ),
        risultato=verifica.sv_terr_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Componente verticale della spinta del terreno (0 se δ=0, attrito terreno-muro nullo).",
    )


def _passo_sh_q(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=True)
    verifica = trova_verifica(output, spinta.nome)
    return Passo(
        simbolo="SH_q", formula=f"K_a * q * γ_Q * H * cos(δ_d){termine}",
        valori=(
            Valore(simbolo="K_a", valore=spinta.ka, descrizione="coefficiente di spinta attiva, derivato sopra"),
            Valore(simbolo="q", valore=inputs.q_kN_m2, unita="kN/m2", descrizione="sovraccarico variabile a tergo del muro"),
            Valore(simbolo="γ_Q", valore=spinta.gamma_q, descrizione="coefficiente parziale sul sovraccarico variabile"),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m"),
            Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad"),
            *_valori_kv_gamma_e(inputs, spinta),
        ),
        risultato=verifica.sh_q_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Componente orizzontale della spinta dovuta al sovraccarico.",
    )


def _passo_sv_q(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=True)
    verifica = trova_verifica(output, spinta.nome)
    return Passo(
        simbolo="SV_q", formula=f"K_a * q * γ_Q * H * sin(δ_d){termine}",
        valori=(
            Valore(simbolo="K_a", valore=spinta.ka),
            Valore(simbolo="q", valore=inputs.q_kN_m2, unita="kN/m2"),
            Valore(simbolo="γ_Q", valore=spinta.gamma_q),
            Valore(simbolo="H", valore=output.geometria.h_muro_tot_m, unita="m"),
            Valore(simbolo="δ_d", valore=spinta.delta_d_rad, unita="rad"),
            *_valori_kv_gamma_e(inputs, spinta),
        ),
        risultato=verifica.sv_q_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Componente verticale della spinta dovuta al sovraccarico (0 se δ=0).",
    )


def _passo_w_muro(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=False)
    valori = [
        Valore(simbolo="γ_cls", valore=inputs.gamma_cls_kN_m3, unita="kN/m3", descrizione="peso di volume del calcestruzzo"),
        Valore(simbolo="A_muro", valore=output.geometria.a_muro_m2, unita="m2", descrizione="area composita della sezione del muro (fondazione + fusto + rastremazione), non ristata qui"),
        Valore(simbolo="γ_G,muro", valore=spinta.gamma_g_muro, descrizione="coefficiente parziale sul peso proprio del muro"),
    ]
    if spinta.sismica:
        valori.append(Valore(simbolo="k_v", valore=spinta.kv, descrizione="coefficiente sismico verticale, derivato sopra: scala anche il peso proprio del monolite (EN1998-5 §7.3.2.2(2)P)"))
    return Passo(
        simbolo="W_muro", formula=f"γ_cls * A_muro * γ_G,muro{termine}",
        valori=tuple(valori), risultato=spinta.w_muro_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Peso proprio del muro (fusto + fondazione).",
    )


def _passo_m_muro(output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    return Passo(
        simbolo="M_muro", formula="W_muro * x_muro",
        valori=(
            Valore(simbolo="W_muro", valore=spinta.w_muro_kN, unita="kN", descrizione="peso proprio del muro, derivato sopra"),
            Valore(simbolo="x_muro", valore=output.geometria.x_muro_m, unita="m", descrizione="baricentro composito del muro dal polo di ribaltamento, non ristato qui"),
        ),
        risultato=spinta.m_muro_kNm, unita="kNm", clausola="NTC2018 §6.5.3.1.1",
        nota="Momento stabilizzante del peso proprio del muro rispetto alla punta di valle.",
    )


def _passo_w_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    termine = _termine_sismico(spinta, con_gamma_e=False)
    valori = [
        Valore(simbolo="γ_terr", valore=inputs.gamma_terr_sat_kN_m3, unita="kN/m3", descrizione="peso di volume del terreno saturo"),
        Valore(simbolo="A_terr", valore=output.geometria.a_terr_m2, unita="m2", descrizione="area del cuneo di terreno a tergo, derivata in Geometria e parametri sismici"),
        Valore(simbolo="γ_G,terr", valore=spinta.gamma_g_terr, descrizione="coefficiente parziale sul peso del terreno"),
    ]
    if spinta.sismica:
        valori.append(Valore(simbolo="k_v", valore=spinta.kv, descrizione="coefficiente sismico verticale, derivato sopra"))
    return Passo(
        simbolo="W_terr", formula=f"γ_terr * A_terr * γ_G,terr{termine}",
        valori=tuple(valori), risultato=spinta.w_terr_kN, unita="kN", clausola="NTC2018 §6.5.3.1.1",
        nota="Peso del cuneo di terreno a tergo del muro.",
    )


def _passo_m_terr(output: MuroSostegnoOutput, spinta: SpintaCombo) -> Passo:
    return Passo(
        simbolo="M_terr", formula="W_terr * x_terr",
        valori=(
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato sopra"),
            Valore(simbolo="x_terr", valore=output.geometria.x_terr_m, unita="m", descrizione="baricentro del terreno, derivato in Geometria e parametri sismici"),
        ),
        risultato=spinta.m_terr_kNm, unita="kNm", clausola="NTC2018 §6.5.3.1.1",
        nota="Momento stabilizzante del peso del terreno rispetto alla punta di valle.",
    )

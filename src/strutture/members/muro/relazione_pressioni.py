"""Verified restatement (docs/architecture-phase2.md) of `pressioni_terreno.py` (EC7 Annex D.1 /
NTC2018 §6.4.2.1): eccentricity of the three vertical-load terms about the footing centre, the
resultant eccentricity e = Mtot/Ntot, the effective width B* and the trapezoidal/triangular contact
pressure — for the SAME governing combination as `relazione_stabilita.py`
(`relazione_comune.combo_governante_stabilita`, docs/architecture-phase2.md §5), reusing its
already-derived M_RIB/N_TOT and `relazione_spinta.py`'s W_muro/W_terr/SV_q/SV_terr rather than
re-deriving them. There is no `Check` for these values (`tool.py` never builds one — only the
CalcError guard on |e|>B/2, unreachable once `pressioni_terreno` has already returned): the
|e| vs B/6 comparison below is informative (which branch of the pressure diagram applies), not a
pass/fail verification, and its `nota` says so.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import MuroSostegnoOutput, NomeCombo, PressioniCombo
from .relazione_comune import (
    combo_governante_stabilita,
    nome_combo_leggibile,
    trova_pressioni,
    trova_spinta,
    trova_verifica,
)

CLAUSE_ECCENTRICITA = "EC7 Annex D.1 / NTC2018 §6.4.2.1"


def traccia_pressioni(output: MuroSostegnoOutput) -> Traccia:
    """8 passi (9 quando la risultante cade fuori dal nocciolo: +B_star — review finding
    MISSING_STEP): e_muro, e_terr, e_sv, M_TOT, e, confronto |e| vs B/6 (informativo), [B_star,]
    p_valle, p_monte."""
    nome = combo_governante_stabilita(output)
    b_fond_m = output.geometria.b_fond_m
    pressioni = trova_pressioni(output, nome)
    passi = (
        _passo_e_muro(output, nome, pressioni), _passo_e_terr(output, nome, pressioni), _passo_e_sv(output, nome, pressioni),
        _passo_m_tot(output, nome, pressioni), _passo_e(output, nome, pressioni),
        _passo_confronto_nocciolo(pressioni, b_fond_m),
    )
    if not pressioni.entro_nocciolo:
        passi = (*passi, _passo_b_star(pressioni, b_fond_m))
    passi = (*passi, _passo_p_valle(pressioni, b_fond_m), _passo_p_monte(pressioni, b_fond_m))
    return Traccia(
        titolo=f"Pressioni sul terreno di fondazione — combinazione governante {nome_combo_leggibile(nome)}",
        passi=passi,
    )


def _passo_b_star(pressioni: PressioniCombo, b_fond_m: float) -> Passo:
    """Review finding (MISSING_STEP): B* entrava in p_valle/p_monte come numero nudo, con
    l'assunzione "risultante fuori dal nocciolo -> diagramma triangolare" invisibile (la
    `descrizione` non è resa in stampa, docs/architecture-phase2.md §5)."""
    return Passo(
        simbolo="B_star", formula="3 * (B / 2 - abs(e))",
        valori=(
            Valore(simbolo="B", valore=b_fond_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="e", valore=pressioni.eccentricita_m, unita="m", descrizione="eccentricità della risultante, derivata sopra"),
        ),
        risultato=pressioni.b_star_m, unita="m", clausola=CLAUSE_ECCENTRICITA,
        nota="Larghezza efficace: la risultante cade fuori dal nocciolo d'inerzia (|e| > B/6), diagramma di pressione triangolare.",
    )


def _passo_e_muro(output: MuroSostegnoOutput, nome: NomeCombo, pressioni: PressioniCombo) -> Passo:
    return Passo(
        simbolo="e_muro", formula="B / 2 - x_muro",
        valori=(
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m", descrizione="larghezza della fondazione, derivata in Geometria e parametri sismici"),
            Valore(simbolo="x_muro", valore=output.geometria.x_muro_m, unita="m", descrizione="baricentro del muro, citato in Spinta attiva e pesi stabilizzanti"),
        ),
        risultato=pressioni.e_muro_m, unita="m", clausola=CLAUSE_ECCENTRICITA,
        nota="Eccentricità del peso del muro rispetto al centro della fondazione.",
    )


def _passo_e_terr(output: MuroSostegnoOutput, nome: NomeCombo, pressioni: PressioniCombo) -> Passo:
    return Passo(
        simbolo="e_terr", formula="B / 2 - x_terr",
        valori=(
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m"),
            Valore(simbolo="x_terr", valore=output.geometria.x_terr_m, unita="m", descrizione="baricentro del terreno, derivato in Geometria e parametri sismici"),
        ),
        risultato=pressioni.e_terr_m, unita="m", clausola=CLAUSE_ECCENTRICITA,
        nota="Eccentricità del peso del terreno rispetto al centro della fondazione.",
    )


def _passo_e_sv(output: MuroSostegnoOutput, nome: NomeCombo, pressioni: PressioniCombo) -> Passo:
    return Passo(
        simbolo="e_sv", formula="B / 2 - x_sv",
        valori=(
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m"),
            Valore(simbolo="x_sv", valore=output.geometria.x_sv_m, unita="m", descrizione="braccio della spinta verticale (coincide con x_terr per definizione geometrica)"),
        ),
        risultato=pressioni.e_sv_m, unita="m", clausola=CLAUSE_ECCENTRICITA,
        nota="Eccentricità della spinta verticale totale rispetto al centro della fondazione.",
    )


def _passo_m_tot(output: MuroSostegnoOutput, nome: NomeCombo, pressioni: PressioniCombo) -> Passo:
    verifica = trova_verifica(output, nome)
    spinta = trova_spinta(output, nome)
    return Passo(
        simbolo="M_TOT", formula="M_RIB + W_muro * e_muro + W_terr * e_terr + (SV_q + SV_terr) * e_sv",
        valori=(
            Valore(simbolo="M_RIB", valore=verifica.m_rib_kNm, unita="kNm", descrizione="momento ribaltante, derivato in Ribaltamento e scorrimento"),
            Valore(simbolo="W_muro", valore=spinta.w_muro_kN, unita="kN", descrizione="peso del muro, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="e_muro", valore=pressioni.e_muro_m, unita="m", descrizione="eccentricità del muro, derivata sopra"),
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="e_terr", valore=pressioni.e_terr_m, unita="m", descrizione="eccentricità del terreno, derivata sopra"),
            Valore(simbolo="SV_q", valore=verifica.sv_q_kN, unita="kN", descrizione="spinta verticale del sovraccarico"),
            Valore(simbolo="SV_terr", valore=verifica.sv_terr_kN, unita="kN", descrizione="spinta verticale del terreno"),
            Valore(simbolo="e_sv", valore=pressioni.e_sv_m, unita="m", descrizione="eccentricità della spinta verticale, derivata sopra"),
        ),
        risultato=pressioni.m_tot_kNm, unita="kNm", clausola=CLAUSE_ECCENTRICITA,
        nota="Momento totale rispetto al centro della fondazione: momento ribaltante più i tre momenti di eccentricità.",
    )


def _passo_e(output: MuroSostegnoOutput, nome: NomeCombo, pressioni: PressioniCombo) -> Passo:
    verifica = trova_verifica(output, nome)
    return Passo(
        simbolo="e", formula="M_TOT / N_TOT",
        valori=(
            Valore(simbolo="M_TOT", valore=pressioni.m_tot_kNm, unita="kNm", descrizione="momento totale, derivato sopra"),
            Valore(simbolo="N_TOT", valore=verifica.n_tot_kN, unita="kN", descrizione="risultante verticale, derivata in Ribaltamento e scorrimento"),
        ),
        risultato=pressioni.eccentricita_m, unita="m", clausola=CLAUSE_ECCENTRICITA,
        nota="Eccentricità della risultante rispetto al centro della fondazione.",
    )


def _passo_confronto_nocciolo(pressioni: PressioniCombo, b_fond_m: float) -> Passo:
    soddisfatta = pressioni.entro_nocciolo
    return Passo(
        simbolo="|e| entro il nocciolo", formula="abs(e) <= B / 6",
        valori=(
            Valore(simbolo="e", valore=pressioni.eccentricita_m, unita="m", descrizione="eccentricità della risultante, derivata sopra"),
            Valore(simbolo="B", valore=b_fond_m, unita="m", descrizione="larghezza della fondazione"),
        ),
        risultato=abs(pressioni.eccentricita_m), unita="m", clausola=CLAUSE_ECCENTRICITA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Confronto informativo, non un Check autonomo: determina se la sezione è interamente compressa "
             "(diagramma trapezoidale) oppure parzializzata (diagramma triangolare, usato sotto).",
    )


def _passo_p_valle(pressioni: PressioniCombo, b_fond_m: float) -> Passo:
    if pressioni.b_star_m == 0.0:
        return Passo(
            simbolo="p_valle", formula="N_TOT / B + 6 * M_TOT / B^2",
            valori=(
                Valore(simbolo="N_TOT", valore=pressioni.n_tot_kN, unita="kN"),
                Valore(simbolo="B", valore=b_fond_m, unita="m"),
                Valore(simbolo="M_TOT", valore=pressioni.m_tot_kNm, unita="kNm"),
            ),
            risultato=pressioni.p_valle_kPa, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
            nota="Sezione interamente compressa (diagramma trapezoidale).",
        )
    if pressioni.m_tot_kNm < 0:
        return Passo(
            simbolo="p_valle", formula="0", valori=(),
            risultato=0.0, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
            nota="Sollevamento del lembo di valle (diagramma triangolare, risultante spostata verso monte).",
        )
    return Passo(
        simbolo="p_valle", formula="2 * N_TOT / B_star",
        valori=(
            Valore(simbolo="N_TOT", valore=pressioni.n_tot_kN, unita="kN"),
            Valore(simbolo="B_star", valore=pressioni.b_star_m, unita="m", descrizione="larghezza efficace, derivata sopra"),
        ),
        risultato=pressioni.p_valle_kPa, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
        nota="Sezione parzializzata (diagramma triangolare), lembo di monte sollevato.",
    )


def _passo_p_monte(pressioni: PressioniCombo, b_fond_m: float) -> Passo:
    if pressioni.b_star_m == 0.0:
        return Passo(
            simbolo="p_monte", formula="N_TOT / B - 6 * M_TOT / B^2",
            valori=(
                Valore(simbolo="N_TOT", valore=pressioni.n_tot_kN, unita="kN"),
                Valore(simbolo="B", valore=b_fond_m, unita="m"),
                Valore(simbolo="M_TOT", valore=pressioni.m_tot_kNm, unita="kNm"),
            ),
            risultato=pressioni.p_monte_kPa, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
            nota="Sezione interamente compressa (diagramma trapezoidale).",
        )
    if pressioni.m_tot_kNm < 0:
        return Passo(
            simbolo="p_monte", formula="2 * N_TOT / B_star",
            valori=(
                Valore(simbolo="N_TOT", valore=pressioni.n_tot_kN, unita="kN"),
                Valore(simbolo="B_star", valore=pressioni.b_star_m, unita="m", descrizione="larghezza efficace, derivata sopra"),
            ),
            risultato=pressioni.p_monte_kPa, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
            nota="Sezione parzializzata (diagramma triangolare), lembo di valle sollevato.",
        )
    return Passo(
        simbolo="p_monte", formula="0", valori=(),
        risultato=0.0, unita="kPa", clausola=CLAUSE_ECCENTRICITA,
        nota="Sollevamento del lembo di monte (diagramma triangolare, risultante spostata verso valle).",
    )

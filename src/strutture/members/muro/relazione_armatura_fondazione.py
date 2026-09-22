"""Verified restatement (docs/architecture-phase2.md) of `armatura_fondazione_valle.py` (toe/mancia
cantilever, NTC2018 §6.5.3.1.1/§4.1.2) and `armatura_fondazione_monte.py` (heel/tacco cantilever,
same clauses), one Traccia each, for the combination that governs EACH design
(`ArmaturaFondazione{Valle,Monte}Result.combo_governante`, the max-As.nec row — nothing to
re-derive there; the two may differ from each other and from `relazione_stabilita.py`'s).

`p*`/`p**` (the pressure at the cantilever root, `pressione_interpolata_kPa`) ARE now restated
(review finding MISSING_STEP: they used to enter MEd.p.1/MEd.tot as bare numbers with the
"resultant outside the kern -> triangular diagram" assumption invisible) — each printing only the
branch actually active (`b_star_m == 0` vs `!= 0`), the same precedent `ca_pilastri.relazione_taglio
._passo_ac` uses for its own selector formula. The residual pressure-wedge moment terms (MEd.p.2 of
valle, MEd.p of monte) stay cited directly (with a `descrizione` naming the diagram they come
from), same precedent as `ca_travi.relazione_sle`'s σ_s,limite: only MEd.p.1 of valle is restated,
because it collapses to a single `min(...)` call regardless of branch (`momento_pressione_1_kNm`,
verified against the source). The linear self-weight/backfill/surcharge moment terms are restated
in full. `d` (the same formula for both cantilevers, `copertura_fondazione_m` "comune a valle e
monte") is re-derived in each Traccia so every Traccia stays self-contained.

`ArmaturaFondazioneValleResult.as_nec_cm2_m`/`ArmaturaFondazioneMonteResult.as_nec_cm2_m` share
their UI `symbol` hint ("A_s,nec") with `ArmaturaParamentoResult.as_nec_cm2_m` (`models.py`,
unrelated to this wave's `relazione`) — of the three, only the LAST one `MuroSostegnoOutput`
exposes (fondazione di monte, `model_fields` traversal order) can carry the bare "A_s,nec" symbol
without the harness's global highlight cross-check picking up the wrong combinazione's value;
valle's step below is labelled "A_s,nec (valle)" instead, monte's keeps the bare symbol.
"""
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import MuroSostegnoInput, MuroSostegnoOutput
from .relazione_armatura_minima import passi_armatura_minima
from .relazione_comune import trova_pressioni, trova_spinta, trova_verifica

CLAUSE_MOMENTO = "NTC2018 §6.5.3.1.1"
CLAUSE_ARMATURA = "NTC2018 §4.1.2"


def traccia_armatura_fondazione_valle(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """6 passi: p*, MEd.p.1, MEd.fond, MEd.tot, d, As.nec."""
    risultato = output.armatura_fondazione_valle
    nome = risultato.combo_governante
    spinta = trova_spinta(output, nome)
    pressioni = trova_pressioni(output, nome)
    combo = next(c for c in risultato.combinazioni if c.nome == nome)
    fyd_MPa = rebar_properties(inputs.grado_acciaio).fyd_MPa
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    return Traccia(
        titolo=f"Armatura della fondazione di valle (mancia) — combinazione governante {nome}",
        passi=(
            _passo_p_star(inputs, output, pressioni, combo),
            _passo_m_ed_p1(inputs, pressioni, combo),
            _passo_m_ed_fond_valle(inputs, spinta, combo),
            _passo_m_ed_tot_valle(combo),
            _passo_d(inputs, d_m),
            _passo_as_nec(combo, fyd_MPa, d_m, simbolo="A_s,nec (valle)"),
            *passi_armatura_minima(inputs, risultato, d_m=d_m, suffisso="valle"),
        ),
    )


def traccia_armatura_fondazione_monte(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """8 passi: p**, MEd.terr, MEd.SV, MEd.fond, MEd.tot, d, As.nec (MEd.p citato direttamente)."""
    risultato = output.armatura_fondazione_monte
    nome = risultato.combo_governante
    spinta = trova_spinta(output, nome)
    verifica = trova_verifica(output, nome)
    pressioni = trova_pressioni(output, nome)
    combo = next(c for c in risultato.combinazioni if c.nome == nome)
    fyd_MPa = rebar_properties(inputs.grado_acciaio).fyd_MPa
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    return Traccia(
        titolo=f"Armatura della fondazione di monte (tacco) — combinazione governante {nome}",
        passi=(
            _passo_p_star_star(inputs, output, pressioni, combo),
            _passo_m_ed_terr(inputs, output, spinta, combo),
            _passo_m_ed_sv(inputs, output, verifica, combo),
            _passo_m_ed_fond_monte(inputs, spinta, combo),
            _passo_m_ed_tot_monte(combo),
            _passo_d(inputs, d_m),
            _passo_as_nec(combo, fyd_MPa, d_m),
            *passi_armatura_minima(inputs, risultato, d_m=d_m, suffisso="monte"),
        ),
    )


def _passo_p_star(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, pressioni, combo) -> Passo:
    """Review finding (MISSING_STEP): p* entrava in MEd.p.1/MEd.tot come numero nudo, con
    l'assunzione "risultante fuori dal nocciolo -> diagramma triangolare, B*>0" invisibile (solo la
    `descrizione`, non resa in stampa, la dichiarava). Stampa solo il ramo effettivamente attivo,
    come `ca_pilastri.relazione_taglio._passo_ac` fa per il proprio selettore."""
    b_fond_m = output.geometria.b_fond_m
    if pressioni.b_star_m == 0.0:
        formula = "p_monte + (p_valle - p_monte) * (B - x_star) / B"
        valori = (
            Valore(simbolo="p_monte", valore=pressioni.p_monte_kPa, unita="kPa", descrizione="pressione sul terreno lato monte, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="p_valle", valore=pressioni.p_valle_kPa, unita="kPa", descrizione="pressione sul terreno lato valle, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="B", valore=b_fond_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="x_star", valore=inputs.b_valle_m, unita="m", descrizione="ascissa dell'incastro della mensola di valle (=B_valle)"),
        )
        nota = "Pressione all'incastro della mensola di valle, sezione interamente compressa (diagramma trapezoidale)."
    else:
        formula = "p_valle * (B_star - x_star) / B_star"
        valori = (
            Valore(simbolo="p_valle", valore=pressioni.p_valle_kPa, unita="kPa", descrizione="pressione sul terreno lato valle, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="B_star", valore=pressioni.b_star_m, unita="m", descrizione="larghezza efficace, derivata in Pressioni sul terreno di fondazione (risultante fuori dal nocciolo)"),
            Valore(simbolo="x_star", valore=inputs.b_valle_m, unita="m", descrizione="ascissa dell'incastro della mensola di valle (=B_valle)"),
        )
        nota = "Pressione all'incastro della mensola di valle, sezione parzializzata (diagramma triangolare)."
    return Passo(simbolo="p_star", formula=formula, valori=valori, risultato=combo.p_star_kPa, unita="kPa", clausola=CLAUSE_MOMENTO, nota=nota)


def _passo_p_star_star(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, pressioni, combo) -> Passo:
    """Review finding (MISSING_STEP): stesso difetto di p* (mensola di valle), per p** (mensola di
    monte). Il terzo ramo di `armatura_fondazione_monte.pressione_interpolata_kPa` (B*=0 escluso,
    B* > -(B-B_monte) falso) non è mai raggiungibile con B*>=0 e B_monte<B (vedi il docstring della
    funzione), quindi restano solo i due rami stampati qui."""
    b_fond_m = output.geometria.b_fond_m
    if pressioni.b_star_m == 0.0:
        formula = "p_monte + B_monte * (p_valle - p_monte) / B"
        valori = (
            Valore(simbolo="p_monte", valore=pressioni.p_monte_kPa, unita="kPa", descrizione="pressione sul terreno lato monte, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="B_monte", valore=inputs.b_monte_m, unita="m", descrizione="larghezza della fondazione lato monte (tacco)"),
            Valore(simbolo="p_valle", valore=pressioni.p_valle_kPa, unita="kPa", descrizione="pressione sul terreno lato valle, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="B", valore=b_fond_m, unita="m", descrizione="larghezza della fondazione"),
        )
        nota = "Pressione all'incastro della mensola di monte, sezione interamente compressa (diagramma trapezoidale)."
    else:
        formula = "(B_star - (B - B_monte)) * p_valle / B_star"
        valori = (
            Valore(simbolo="B_star", valore=pressioni.b_star_m, unita="m", descrizione="larghezza efficace, derivata in Pressioni sul terreno di fondazione (risultante fuori dal nocciolo)"),
            Valore(simbolo="B", valore=b_fond_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="B_monte", valore=inputs.b_monte_m, unita="m", descrizione="larghezza della fondazione lato monte (tacco)"),
            Valore(simbolo="p_valle", valore=pressioni.p_valle_kPa, unita="kPa", descrizione="pressione sul terreno lato valle, derivata in Pressioni sul terreno di fondazione"),
        )
        nota = "Pressione all'incastro della mensola di monte, sezione parzializzata (diagramma triangolare)."
    return Passo(simbolo="p_star_star", formula=formula, valori=valori, risultato=combo.p_star_star_kPa, unita="kPa", clausola=CLAUSE_MOMENTO, nota=nota)


def _passo_m_ed_p1(inputs: MuroSostegnoInput, pressioni, combo) -> Passo:
    return Passo(
        simbolo="M_Ed,p1", formula="min(p_star, p_valle) * B_valle^2 / 2",
        valori=(
            Valore(simbolo="p_star", valore=combo.p_star_kPa, unita="kPa", descrizione="pressione all'incastro della mensola di valle, derivata sopra"),
            Valore(simbolo="p_valle", valore=pressioni.p_valle_kPa, unita="kPa", descrizione="pressione sul terreno lato valle, derivata in Pressioni sul terreno di fondazione"),
            Valore(simbolo="B_valle", valore=inputs.b_valle_m, unita="m", descrizione="larghezza della fondazione lato valle (mancia)"),
        ),
        risultato=combo.m_ed_p1_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento del blocco di pressione rettangolare/triangolare inferiore.",
    )


def _passo_m_ed_fond_valle(inputs: MuroSostegnoInput, spinta, combo) -> Passo:
    return Passo(
        simbolo="M_Ed,fond", formula="-γ_G,muro * s_fond * γ_cls * B_valle^2 / 2",
        valori=(
            Valore(simbolo="γ_G,muro", valore=spinta.gamma_g_muro, descrizione="coefficiente parziale sul peso proprio del muro"),
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m", descrizione="spessore della fondazione"),
            Valore(simbolo="γ_cls", valore=inputs.gamma_cls_kN_m3, unita="kN/m3", descrizione="peso di volume del calcestruzzo"),
            Valore(simbolo="B_valle", valore=inputs.b_valle_m, unita="m"),
        ),
        risultato=combo.m_ed_fond_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento del peso proprio della mensola di valle (favorevole, segno negativo).",
    )


def _passo_m_ed_tot_valle(combo) -> Passo:
    return Passo(
        simbolo="M_Ed,tot", formula="M_Ed,p1 + M_Ed,p2 + M_Ed,fond",
        valori=(
            Valore(simbolo="M_Ed,p1", valore=combo.m_ed_p1_kNm, unita="kNm", descrizione="momento del blocco di pressione, derivato sopra"),
            Valore(simbolo="M_Ed,p2", valore=combo.m_ed_p2_kNm, unita="kNm", descrizione="momento del cuneo di pressione residuo, diagramma a tre rami (p*/p_valle/B*), non ristato qui"),
            Valore(simbolo="M_Ed,fond", valore=combo.m_ed_fond_kNm, unita="kNm", descrizione="momento del peso proprio della mensola, derivato sopra"),
        ),
        risultato=combo.m_ed_tot_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento flettente totale all'incastro della mensola di valle.",
    )


def _passo_m_ed_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, spinta, combo) -> Passo:
    return Passo(
        simbolo="M_Ed,terr", formula="W_terr * (B_monte - (B - x_terr))",
        valori=(
            Valore(simbolo="W_terr", valore=spinta.w_terr_kN, unita="kN", descrizione="peso del terreno, derivato in Spinta attiva e pesi stabilizzanti"),
            Valore(simbolo="B_monte", valore=inputs.b_monte_m, unita="m", descrizione="larghezza della fondazione lato monte (tacco)"),
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m", descrizione="larghezza della fondazione"),
            Valore(simbolo="x_terr", valore=output.geometria.x_terr_m, unita="m", descrizione="baricentro del terreno, derivato in Geometria e parametri sismici"),
        ),
        risultato=combo.m_ed_terr_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento del peso del cuneo di terreno a tergo, rispetto all'incastro della mensola di monte.",
    )


def _passo_m_ed_sv(inputs: MuroSostegnoInput, output: MuroSostegnoOutput, verifica, combo) -> Passo:
    return Passo(
        simbolo="M_Ed,SV", formula="(SV_q + SV_terr) * (x_sv - (B - B_monte))",
        valori=(
            Valore(simbolo="SV_q", valore=verifica.sv_q_kN, unita="kN", descrizione="spinta verticale del sovraccarico"),
            Valore(simbolo="SV_terr", valore=verifica.sv_terr_kN, unita="kN", descrizione="spinta verticale del terreno"),
            Valore(simbolo="x_sv", valore=output.geometria.x_sv_m, unita="m", descrizione="braccio della spinta verticale"),
            Valore(simbolo="B", valore=output.geometria.b_fond_m, unita="m"),
            Valore(simbolo="B_monte", valore=inputs.b_monte_m, unita="m"),
        ),
        risultato=combo.m_ed_sv_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento della componente verticale della spinta, rispetto all'incastro della mensola di monte.",
    )


def _passo_m_ed_fond_monte(inputs: MuroSostegnoInput, spinta, combo) -> Passo:
    return Passo(
        simbolo="M_Ed,fond", formula="γ_G,muro * γ_cls * s_fond * B_monte^2 / 2",
        valori=(
            Valore(simbolo="B_monte", valore=inputs.b_monte_m, unita="m"),
            Valore(simbolo="γ_G,muro", valore=spinta.gamma_g_muro, descrizione="coefficiente parziale sul peso proprio del muro"),
            Valore(simbolo="γ_cls", valore=inputs.gamma_cls_kN_m3, unita="kN/m3"),
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m"),
        ),
        risultato=combo.m_ed_fond_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento del peso proprio della soletta di monte.",
    )


def _passo_m_ed_tot_monte(combo) -> Passo:
    return Passo(
        simbolo="M_Ed,tot", formula="M_Ed,p + M_Ed,terr + M_Ed,SV + M_Ed,fond",
        valori=(
            Valore(simbolo="M_Ed,p", valore=combo.m_ed_p_kNm, unita="kNm", descrizione="momento del diagramma di pressione sotto la mensola di monte, tre rami secondo la posizione di p** rispetto a p_monte/B*, non ristato qui"),
            Valore(simbolo="M_Ed,terr", valore=combo.m_ed_terr_kNm, unita="kNm", descrizione="momento del peso del terreno, derivato sopra"),
            Valore(simbolo="M_Ed,SV", valore=combo.m_ed_sv_kNm, unita="kNm", descrizione="momento della spinta verticale, derivato sopra"),
            Valore(simbolo="M_Ed,fond", valore=combo.m_ed_fond_kNm, unita="kNm", descrizione="momento del peso proprio della soletta, derivato sopra"),
        ),
        risultato=combo.m_ed_tot_kNm, unita="kNm", clausola=CLAUSE_MOMENTO,
        nota="Momento flettente totale all'incastro della mensola di monte.",
    )


def _passo_d(inputs: MuroSostegnoInput, d_m: float) -> Passo:
    return Passo(
        simbolo="d", formula="s_fond - c_fond",
        valori=(
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m", descrizione="spessore della fondazione"),
            Valore(simbolo="c_fond", valore=inputs.copertura_fondazione_m, unita="m", descrizione="copriferro asse barre trasversali della fondazione"),
        ),
        risultato=d_m, unita="m", clausola=CLAUSE_ARMATURA,
        nota="Altezza utile della sezione della fondazione.",
    )


def _passo_as_nec(combo, fyd_MPa: float, d_m: float, *, simbolo: str = "A_s,nec") -> Passo:
    return Passo(
        simbolo=simbolo, formula="M_Ed,tot * 10000 / (k_z * d * 1000 * f_yd)",
        valori=(
            Valore(simbolo="M_Ed,tot", valore=combo.m_ed_tot_kNm, unita="kNm", descrizione="momento flettente totale, derivato sopra"),
            Valore(simbolo="k_z", valore=0.9, descrizione="rapporto jd/d assunto, flessione semplificata NTC2018 §4.1.2"),
            Valore(simbolo="d", valore=d_m, unita="m", descrizione="altezza utile, derivata sopra"),
            Valore(simbolo="f_yd", valore=fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio"),
        ),
        risultato=combo.as_nec_cm2_m, unita="cm2/m", clausola=CLAUSE_ARMATURA,
        nota="Area di armatura necessaria (può risultare negativa se MEd,tot è favorevole su questa combinazione).",
    )

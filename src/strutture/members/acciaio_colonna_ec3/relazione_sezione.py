"""Verified restatement (docs/architecture-phase2.md) of `materiale.py` (grade lookup, f_yd) and of
the plastic/elastic reference resistances of `sezione.py` (N_pl,Rd, M_pl or M_c,{y,z},Rd —
column-check!Q41, Q39, Q40), the DESIGN-strength values later reused by the interaction checks
(`relazione_interazione.py`, `relazione_interazione_semplificata.py`) exactly as computed, never
re-derived. Standard mode only: `materiale.risolvi_materiale` always resolves γ_M0/γ_M1 to the EC3
default unless the user overrides them (never the legacy hardcoded-1 branch, see `materiale.py`).

The section CLASS itself (`classe_sezione`) is a direct user input on this sheet — EN1993-1-1 §5.5/
Tab. 5.2 classification from c/t ratios is not computed anywhere in this package (`sezione.py`'s own
docstring already documents the related class-4 gap) — so it is restated as given, not derived, with
a `nota` saying so; it governs the W_pl/W_el choice every later formula in this package makes.

`M_pl,{y,z},Rd`/`M_c,{y,z},Rd` (`relazione_comune.simbolo_momento_rd`): classes 1-2 use the plastic
modulus, genuinely "M_pl"; classes 3-4 use the elastic modulus (`modulo_flessionale`) — calling that
"M_pl" would be self-contradictory (review finding WRONG_CLAUSE: the tool's own example is class 3,
so its trace prints "M_c,y,Rd = W_el,y·f_yd", never "M_pl,y,Rd = W_el,y·f_yd").
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .relazione_comune import N_A_KN, NMM_A_KNM, modulo_flessionale, simbolo_momento_rd
from .results import ColonnaEc3Output
from .sezione import numero_classe


def traccia_sezione(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """5 passi: f_yd, classe (dato di ingresso), N_pl,Rd, M_pl/M_c,y,Rd, M_pl/M_c,z,Rd."""
    classe_num = numero_classe(inputs.classe_sezione)
    return Traccia(
        titolo="Materiali e resistenze plastiche di riferimento",
        passi=(
            _passo_fyd(output), _passo_classe(inputs, classe_num),
            _passo_npl_rd(inputs, output), _passo_mpl_rd(inputs, output, classe_num, "y"),
            _passo_mpl_rd(inputs, output, classe_num, "z"),
        ),
    )


def _passo_fyd(output: ColonnaEc3Output) -> Passo:
    materiali = output.materiali
    return Passo(
        simbolo="f_yd",
        formula="f_yk / γ_M0",
        valori=(
            Valore(simbolo="f_yk", valore=materiali.fyk_MPa, unita="MPa", descrizione=f"tensione caratteristica di snervamento, tabella Materiali (grado {materiali.grado})"),
            Valore(simbolo="γ_M0", valore=materiali.gamma_m0, unita="-", descrizione="fattore parziale di sicurezza per la resistenza delle sezioni"),
        ),
        risultato=materiali.fyd_MPa, unita="MPa", clausola="EN1993-1-1 §6.1(1)",
        nota="Tensione di calcolo di snervamento, impiegata in tutte le verifiche di resistenza seguenti.",
    )


def _passo_classe(inputs: ColonnaEc3Input, classe_num: int) -> Passo:
    return Passo(
        simbolo="classe",
        formula="classe_sezione",
        valori=(Valore(simbolo="classe_sezione", valore=float(classe_num), descrizione=f"classe dichiarata come dato di ingresso ({inputs.classe_sezione})"),),
        risultato=float(classe_num), unita="-", clausola="EN1993-1-1 Tab. 5.2",
        nota="Non calcolata da rapporti c/t: è un dato di ingresso del foglio. Governa la scelta fra "
             "modulo di resistenza plastico (classi 1-2) ed elastico (classi 3-4) in tutte le formule seguenti.",
    )


def _passo_npl_rd(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    return Passo(
        simbolo="N_pl,Rd",
        formula="A * f_yd",
        valori=(
            Valore(simbolo="A", valore=inputs.area_mm2, unita="mm2", descrizione="area lorda della sezione"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa", descrizione="calcolato sopra"),
        ),
        risultato=output.sezione.npl_kN, unita="kN", scala=N_A_KN, clausola="EN1993-1-1 §6.2.4(1) eq. (6.10)",
        nota="Resistenza plastica di progetto a compressione/trazione uniforme della sezione lorda; "
             "riferimento per l'interazione semplificata (§6.2.9.1).",
    )


def _passo_mpl_rd(inputs: ColonnaEc3Input, output: ColonnaEc3Output, classe_num: int, asse: str) -> Passo:
    wel_mm3 = inputs.wel_y_mm3 if asse == "y" else inputs.wel_z_mm3
    wpl_mm3 = inputs.wpl_y_mm3 if asse == "y" else inputs.wpl_z_mm3
    simbolo_modulo, modulo = modulo_flessionale(classe_num, wel_mm3, wpl_mm3, asse)
    risultato = output.sezione.mpl_y_kNm if asse == "y" else output.sezione.mpl_z_kNm
    # Classi 1-2: modulo plastico, davvero "M_pl". Classi 3-4: `modulo_flessionale` sceglie il
    # modulo ELASTICO — chiamarlo "M_pl" sarebbe autocontraddittorio (review finding WRONG_CLAUSE):
    # `simbolo_momento_rd` sceglie "M_c,{asse},Rd" in quel caso, come EN1993-1-1 fa per M_c,Rd/M_el,Rd.
    simbolo = simbolo_momento_rd(classe_num, asse)
    return Passo(
        simbolo=simbolo,
        formula=f"{simbolo_modulo} * f_yd",
        valori=(
            Valore(simbolo=simbolo_modulo, valore=modulo, unita="mm3", descrizione=f"modulo di resistenza (classe {classe_num})"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa", descrizione="calcolato sopra"),
        ),
        risultato=risultato, unita="kNm", scala=NMM_A_KNM, clausola="EN1993-1-1 §6.2.5(2) eq. (6.13)/(6.14)",
        nota=f"Momento resistente di progetto (plastico per classe 1-2, elastico per classe 3-4), asse "
             f"{asse}: riferimento per l'interazione N-My-Mz (§6.3.3) e per le verifiche semplificate "
             f"(§6.2.9.1); distinto dal momento resistente a flessione M_Rd,{asse} (§6.2.5/§6.2.8), che "
             f"include l'eventuale riduzione per taglio elevato.",
    )

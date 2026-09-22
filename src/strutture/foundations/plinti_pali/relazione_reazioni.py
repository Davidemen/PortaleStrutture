"""Verified restatement (docs/architecture-phase2.md §6) of Tool-1's pile-reaction envelope
(`inviluppo.py`/`rows.py`, textbook rigid-cap method generalised by `shared.pile_group.
rigid_cap_axial`, EC2 §9.8.1 pile-as-compression-member) and Tool-1's self-weight (`pesi_propri.py`)
— together, `N_max` (highlighted output). `M_x,final`/`M_y,final` (the already-transferred moments
at pile-head level, `output.governante`) are cited directly rather than re-derived from the raw
column-top forces: they carry no `symbol` hint and feed nothing else in this trace, unlike `d`/`z`
in the flexural design, which the architecture brief's own worked example gives their own step
because later formulas reuse them.

Also covers the "Capacità portante del palo" Check(s) (compressione always, trazione only when a
pile is in tension, `output.capacita_trazione is not None`) — a task addition, no sheet cell
(`capacita_pali.py`'s own docstring)."""
from strutture.shared.pile_group import PilePos, pile_coordinates
from strutture.shared.relazione import Passo, Traccia, Valore

from .input import PlintoSuPaliInput
from .models import PlintoSuPaliOutput
from .models_taglio import CapacitaPalo
from .pesi_propri import GAMMA_CALCESTRUZZO_KNM3, peso_proprio_kN
from .relazione_helpers import indice_palo_governante
from .rows import RigaCarico
from .schema import numero_pali


def traccia_reazioni_pali(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> Traccia:
    """3 passi: reazione assiale del palo governante (metodo rigido, N/Mx/My), peso proprio del
    plinto, reazione di progetto N_max (palo governante + quota di peso proprio)."""
    governante = output.governante
    piles = pile_coordinates(inputs.schema_pali, inputs.lx_m, inputs.ly_m)
    i = indice_palo_governante(governante.n_pali_kN)
    n_pali = numero_pali(inputs.schema_pali)
    peso_kN = peso_proprio_kN(inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.gamma_g1, inputs.carico_aggiuntivo_kN)
    passi = (
        _passo_n_pila(governante, piles, i, n_pali),
        _passo_peso_proprio(inputs, peso_kN),
        _passo_n_max(governante, output, n_pali, peso_kN),
    )
    titolo = f"Reazioni sui pali — combinazione governante {governante.combo} (nodo {governante.nodo})"
    return Traccia(titolo=titolo, passi=passi)


def _passo_n_pila(governante: RigaCarico, piles: tuple[PilePos, ...], i: int, n_pali: int) -> Passo:
    """`shared.pile_group.rigid_cap_axial` drops the Mx (My) term entirely — rather than dividing by
    zero — when the pile grid has no spread along Y (X): every pile shares the same y_i (x_i), so a
    rigid cap cannot resist that moment by differential pile axial force alone (see that module's own
    docstring; `tool.py::_warnings` flags this same case for the user). The restated formula mirrors
    that: the term is omitted from the formula text, not silently zeroed inside it."""
    palo = piles[i]
    sum_x2 = sum(p.x_m**2 for p in piles)
    sum_y2 = sum(p.y_m**2 for p in piles)
    termini = ["N / n_pali"]
    valori = [
        Valore(simbolo="N", valore=governante.n_kN, unita="kN", descrizione="carico verticale totale in colonna, combinazione governante"),
        Valore(simbolo="n_pali", valore=float(n_pali), descrizione="numero di pali dello schema"),
    ]
    if sum_y2 > 0:
        termini.append("M_x,final * y_i / Σy2")
        valori += [
            Valore(simbolo="M_x,final", valore=governante.mx_finale_kNm, unita="kNm", descrizione="momento Mx finale in testa ai pali (già trasferito dal taglio e dall'eccentricità di carico)"),
            Valore(simbolo="y_i", valore=palo.y_m, unita="m", descrizione="ordinata del palo più sollecitato rispetto al baricentro del gruppo"),
            Valore(simbolo="Σy2", valore=sum_y2, unita="m2", descrizione="somma dei quadrati delle ordinate di tutti i pali"),
        ]
    if sum_x2 > 0:
        termini.append("M_y,final * x_i / Σx2")
        valori += [
            Valore(simbolo="M_y,final", valore=governante.my_finale_kNm, unita="kNm", descrizione="momento My finale in testa ai pali"),
            Valore(simbolo="x_i", valore=palo.x_m, unita="m", descrizione="ascissa del palo più sollecitato rispetto al baricentro del gruppo"),
            Valore(simbolo="Σx2", valore=sum_x2, unita="m2", descrizione="somma dei quadrati delle ascisse di tutti i pali"),
        ]
    nota = "Reazione assiale del palo più sollecitato, ipotesi di plinto rigido (metodo elastico, EC2 §9.8.1)."
    if sum_y2 <= 0 or sum_x2 <= 0:
        nota += (
            " Lo schema pali non ha sviluppo lungo " + ("Y" if sum_y2 <= 0 else "X")
            + ": il termine corrispondente è assente (nessuna reazione assiale differenziale possibile su quell'asse)."
        )
    return Passo(
        simbolo="N_pila", formula=" + ".join(termini), valori=tuple(valori),
        risultato=governante.n_max_pila_kN, unita="kN", nota=nota,
    )


def _passo_peso_proprio(inputs: PlintoSuPaliInput, peso_kN: float) -> Passo:
    formula = f"A_X * B_Y * H * {GAMMA_CALCESTRUZZO_KNM3:g} * γ_G1"
    valori = [
        Valore(simbolo="A_X", valore=inputs.ax_m, unita="m", descrizione="dimensione in pianta del plinto lungo X"),
        Valore(simbolo="B_Y", valore=inputs.by_m, unita="m", descrizione="dimensione in pianta del plinto lungo Y"),
        Valore(simbolo="H", valore=inputs.h_plinto_m, unita="m", descrizione="altezza del plinto"),
        Valore(simbolo="γ_G1", valore=inputs.gamma_g1, descrizione="coefficiente parziale per il peso proprio"),
    ]
    if inputs.carico_aggiuntivo_kN > 0:
        formula = f"{formula} + G_1"
        valori.append(Valore(simbolo="G_1", valore=inputs.carico_aggiuntivo_kN, unita="kN", descrizione="carico permanente aggiuntivo (rinterro, pavimentazioni)"))
    return Passo(
        simbolo="W", formula=formula, valori=tuple(valori), risultato=peso_kN,
        unita="kN", nota="Peso proprio fattorizzato del plinto, caso sfavorevole (γ_cls=25 kN/m³).",
    )


def _passo_n_max(governante: RigaCarico, output: PlintoSuPaliOutput, n_pali: int, peso_kN: float) -> Passo:
    return Passo(
        simbolo="N_max", formula="N_pila + W / n_pali",
        valori=(
            Valore(simbolo="N_pila", valore=governante.n_max_pila_kN, unita="kN", descrizione="reazione del palo governante, calcolata sopra"),
            Valore(simbolo="W", valore=peso_kN, unita="kN", descrizione="peso proprio del plinto, calcolato sopra"),
            Valore(simbolo="n_pali", valore=float(n_pali)),
        ),
        risultato=output.n_max_pila_kN, unita="kN",
        nota="Reazione di progetto sul palo, quota di peso proprio del plinto inclusa per intero (caso sfavorevole).",
    )


def traccia_capacita_pali(output: PlintoSuPaliOutput) -> Traccia:
    """1 o 2 passi: Check "Capacità portante del palo (compressione)", sempre presente, ed
    eventualmente il Check "... (trazione)" quando un palo risulta teso.

    Review finding (MISSING_STEP): R_c/R_t erano etichettati genericamente come "resistenza
    ammissibile ... dato di ingresso", clausola "Geotecnica" (non una clausola normativa): nulla
    dichiarava se il valore fornito fosse caratteristico (R_c,k) o di progetto (R_c,d) —
    NTC2018 §6.4.3.1.1/Tab. 6.4.II richiede il valore DI PROGETTO (R_c,k·ξ/γ_R); un R_c,k inserito
    per errore renderebbe la verifica non conservativa del 15-35% senza che nulla lo riveli."""
    passi = (_passo_capacita(output.capacita_compressione, "N_max", "compressione", "R_c,d"),)
    if output.capacita_trazione is not None:
        passi = (*passi, _passo_capacita(output.capacita_trazione, "N_min", "trazione", "R_t,d"))
    return Traccia(titolo="Capacità portante assiale dei pali", passi=passi)


def _passo_capacita(capacita: CapacitaPalo, simbolo_domanda: str, nome: str, simbolo_resistenza: str) -> Passo:
    return Passo(
        simbolo=f"{simbolo_domanda}/{simbolo_resistenza}",
        formula=f"{simbolo_domanda} <= {simbolo_resistenza}",
        valori=(
            Valore(simbolo=simbolo_domanda, valore=capacita.domanda_kN, unita="kN", descrizione=f"reazione di progetto sul palo a {nome}"),
            Valore(simbolo=simbolo_resistenza, valore=capacita.resistenza_kN, unita="kN",
                   descrizione=f"resistenza di progetto del palo a {nome} (R_c,d=R_c,k·ξ/γ_R, "
                                "NTC2018 §6.4.3.1.1 Tab. 6.4.II), dato di ingresso: non il valore caratteristico"),
        ),
        risultato=capacita.domanda_kN, unita="kN", clausola="NTC2018 §6.4.3.1.1",
        esito="soddisfatta" if capacita.verificato else "non soddisfatta",
        nota=f"Verifica \"Capacità portante del palo ({nome})\".",
    )

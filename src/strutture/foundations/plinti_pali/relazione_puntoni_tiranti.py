"""Verified restatement (docs/architecture-phase2.md §6) of Tool-3's strut-and-tie verification
(`puntoni_tiranti.py`, EC2 §6.5.2 strut / §6.5.4 node / §6.5.3+§9.8.1 tie), STANDARD mode branches
only (EC2 node coefficients k1=1,0/k2=0,85/k3=0,75, `shared.ec2_strut_tie.sigma_rd_max` defaults;
never the sheet's own non-standard `legacy_compat=True` coefficients).

Dispatched on the pile pattern, mirroring `puntoni_tiranti.py` itself: the 2x2 mechanism (diagonal
strut to every pile, diagonal tie XY + two orthogonal ties X/Y splitting the strut's horizontal
thrust) and the single-row mechanism (one strut, one tie along the row) — `1x1` (direct bearing, no
strut-and-tie mechanism) never reaches this module: `tool.py::run` itself crashes on that schema
before a `relazione` could ever be built (CALCULATION FINDING, see the package's own
`tests/foundations/plinti_pali/test_schizzo.py::test_composizione_schema_1x1` docstring — a
pre-existing bug, not introduced or fixed here).

`w_t`/`w_s`/`A_cs` are folded into ONE step (named `Valore`s with a `descrizione`, not their own
derivation `Passo`, to keep the step budget of this unusually composite tool sane — see
`relazione.py`'s own docstring); `σ_Rd,max` shows BOTH node classes' `k` coefficients in one step,
each named and described (lesson: never fold a normative coefficient into a bare literal)."""
import math

from strutture.shared.ec2_strut_tie.sigma_rd_max import K1_CCC_EN, K2_CCT_EN, K3_CTT_EN
from strutture.shared.relazione import Passo, Traccia, Valore

from .input import PlintoSuPaliInput
from .models import PlintoSuPaliOutput
from .models_puntoni_tiranti import Puntone, PuntoniTiranti, Tirante
from .puntoni_tiranti import K_TIE_XY_FRACTION
from .relazione_comune import fcd_frammento, nu_prime_frammento, valore_fck, valore_fyd, valore_gamma_c
from .schema import grid_counts

EC2_NODO = "EN 1992-1-1 §6.5.4(4)"
EC2_PUNTONE = "EN 1992-1-1 §6.5.2"
EC2_TIRANTE = "EN 1992-1-1 §6.5.3 / §9.8.1"


def traccia_puntoni_tiranti(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> Traccia:
    count_x, count_y = grid_counts(inputs.schema_pali)
    pt = output.puntoni_tiranti
    if count_x == 2 and count_y == 2:
        passi = _passi_2x2(inputs, output, pt)
        titolo = "Puntoni e tiranti — meccanismo diagonale a 4 pali (schema 2x2)"
    else:
        passi = _passi_fila_singola(inputs, output, pt, count_x, count_y)
        titolo = "Puntoni e tiranti — meccanismo a fila singola"
    return Traccia(titolo=titolo, passi=passi)


def _diametro_tirante_principale(inputs: PlintoSuPaliInput) -> float:
    if inputs.schema_pali == "2x2":
        return inputs.diametro_tirante_xy_mm
    count_x, _ = grid_counts(inputs.schema_pali)
    return inputs.diametro_tirante_x_mm if count_x == 2 else inputs.diametro_tirante_y_mm


def _passi_puntone(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, puntone: Puntone, nodo_secondario: str, k_secondario: float, k_nome: str) -> tuple[Passo, ...]:
    fck_MPa, gamma_c = output.materiali.calcestruzzo.fck_MPa, inputs.gamma_c
    return (
        _passo_theta(puntone),
        _passo_fus(output, puntone),
        _passo_acs(inputs, puntone),
        _passo_sigma_rd_max(fck_MPa, gamma_c, puntone, nodo_secondario, k_secondario, k_nome),
        _passo_fns(puntone),
        _passo_check_puntone(puntone),
    )


def _passi_2x2(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, pt: PuntoniTiranti) -> tuple[Passo, ...]:
    assert pt.tirante_xy is not None and pt.tirante_x is not None and pt.tirante_y is not None
    passi = _passi_puntone(inputs, output, pt.puntone, "CTT", K3_CTT_EN, "k_3")
    passo_alpha = _passo_alpha(inputs)
    alpha_rad = math.atan(inputs.ly_m / inputs.lx_m)
    return (
        *passi, passo_alpha,
        _passo_check_tirante_xy(pt.puntone, pt.tirante_xy, output.materiali.acciaio.fyd_MPa),
        _passo_check_tirante_ortogonale("X", pt.puntone, pt.tirante_x, output.materiali.acciaio.fyd_MPa, alpha_rad, "cos"),
        _passo_check_tirante_ortogonale("Y", pt.puntone, pt.tirante_y, output.materiali.acciaio.fyd_MPa, alpha_rad, "sin"),
        _passo_utilizzo_st(output, pt),
    )


def _passi_fila_singola(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, pt: PuntoniTiranti, count_x: int, count_y: int) -> tuple[Passo, ...]:
    tirante = pt.tirante_x if count_x == 2 else pt.tirante_y
    direzione = "X" if count_x == 2 else "Y"
    assert tirante is not None
    passi = _passi_puntone(inputs, output, pt.puntone, "CCT", K2_CCT_EN, "k_2")
    return (*passi, _passo_check_tirante_fila_singola(direzione, pt.puntone, tirante, output.materiali.acciaio.fyd_MPa), _passo_utilizzo_st(output, pt))


def _passo_theta(puntone: Puntone) -> Passo:
    assert puntone.theta_deg is not None
    return Passo(
        simbolo="θ", formula="atan(h_wt2 / L_XY)", scala=180.0 / math.pi,
        valori=(
            Valore(simbolo="h_wt2", valore=puntone.h_wt2_m, unita="m", descrizione="braccio verticale del puntone (altezza plinto meno metà spessore del tirante superiore)"),
            Valore(simbolo="L_XY", valore=puntone.lxy_m, unita="m", descrizione="distanza in pianta dal baricentro del gruppo pali al palo"),
        ),
        risultato=puntone.theta_deg, unita="°", clausola=EC2_PUNTONE,
        nota="Inclinazione reale del puntone diagonale; il floor a 25° del foglio originale non è una "
             "clausola EC2 ed è stato rimosso a favore del valore reale, con una fascia di validità 20°-70° "
             "(non normativa, verifica di sensatezza geometrica).",
    )


def _valore_theta_rad(puntone: Puntone) -> Valore:
    """θ in RADIANTI per ogni uso dentro un argomento trigonometrico di questa Traccia (review
    finding MISLEADING): il passo θ stesso resta in gradi (`_passo_theta`, coerente col simbolo di
    output `Puntone.theta_deg`), ma sostituirlo in gradi dentro sin()/cos() accanto ad α — già in
    radianti — mescolava le due convenzioni sulla stessa riga senza alcun marcatore visibile (il
    grammatica della notazione converte automaticamente solo un identificatore BARE con
    `unita="°"`, non aiuta il lettore umano che legge la sostituzione stampata). Normalizzare ogni
    argomento trigonometrico della Traccia a radianti, come già fa `muro.relazione_spinta`."""
    assert puntone.theta_deg is not None
    return Valore(
        simbolo="θ", valore=math.radians(puntone.theta_deg), unita="rad",
        descrizione="inclinazione del puntone, calcolata sopra (in radianti)",
    )


def _passo_fus(output: PlintoSuPaliOutput, puntone: Puntone) -> Passo:
    return Passo(
        simbolo="F_us", formula="N_max / sin(θ)",
        valori=(
            Valore(simbolo="N_max", valore=output.n_max_pila_kN, unita="kN", descrizione="reazione di progetto sul palo governante, calcolata sopra"),
            _valore_theta_rad(puntone),
        ),
        risultato=puntone.fus_kN, unita="kN", clausola=EC2_PUNTONE,
        nota="Forza di compressione nel puntone diagonale, equilibrio verticale al nodo del palo.",
    )


def _passo_acs(inputs: PlintoSuPaliInput, puntone: Puntone) -> Passo:
    diametro_princ = _diametro_tirante_principale(inputs)
    c_mm = inputs.copriferro_cm * 10.0
    wt_mm = 2.0 * c_mm + 2.0 * max(inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm) + diametro_princ
    return Passo(
        simbolo="A_cs", formula="(w_t * cos(θ) + φ_palo * sin(θ))^2",
        valori=(
            Valore(simbolo="w_t", valore=wt_mm, unita="mm", descrizione="spessore del tirante superiore, w_t=2c+2·max(φ_inf,X;φ_inf,Y)+φ_tirante"),
            _valore_theta_rad(puntone),
            Valore(simbolo="φ_palo", valore=inputs.diametro_pila_mm, unita="mm", descrizione="diametro del palo"),
        ),
        risultato=puntone.acs_mm2, unita="mm2", clausola=EC2_PUNTONE,
        nota="Area della sezione trasversale del puntone (=nodo), proiezione della larghezza w_s sul piano ortogonale al puntone.",
    )


def _passo_sigma_rd_max(fck_MPa: float, gamma_c: float, puntone: Puntone, nodo_secondario: str, k_secondario: float, k_nome: str) -> Passo:
    formula = f"min(k_1 * {nu_prime_frammento()} * {fcd_frammento()}, {k_nome} * {nu_prime_frammento()} * {fcd_frammento()})"
    return Passo(
        simbolo="σ_Rd,max", formula=formula,
        valori=(
            Valore(simbolo="k_1", valore=K1_CCC_EN, descrizione="coefficiente del nodo CCC (puntone-pilastro), EC2 §6.5.4(4)"),
            valore_fck(fck_MPa), valore_gamma_c(gamma_c),
            Valore(simbolo=k_nome, valore=k_secondario, descrizione=f"coefficiente del nodo {nodo_secondario}, EC2 §6.5.4(4)"),
        ),
        risultato=puntone.sigma_rd_max_MPa, unita="N/mm2", clausola=EC2_NODO,
        nota=f"Tensione massima ammissibile nel nodo, minimo fra il nodo CCC (pilastro-puntone, k_1={K1_CCC_EN:g}) "
             f"e il nodo {nodo_secondario} di base ({k_nome}={k_secondario:g}).",
    )


def _passo_fns(puntone: Puntone) -> Passo:
    return Passo(
        simbolo="F_ns", formula="σ_Rd,max * A_cs / 1000",
        valori=(
            Valore(simbolo="σ_Rd,max", valore=puntone.sigma_rd_max_MPa, unita="N/mm2", descrizione="tensione massima ammissibile nel nodo, calcolata sopra"),
            Valore(simbolo="A_cs", valore=puntone.acs_mm2, unita="mm2", descrizione="area della sezione del puntone, calcolata sopra"),
        ),
        risultato=puntone.fns_kN, unita="kN", clausola=EC2_NODO,
        nota="Resistenza di progetto del puntone.",
    )


def _passo_check_puntone(puntone: Puntone) -> Passo:
    return Passo(
        simbolo="F_us/F_ns", formula="F_us <= F_ns",
        valori=(
            Valore(simbolo="F_us", valore=puntone.fus_kN, unita="kN"),
            Valore(simbolo="F_ns", valore=puntone.fns_kN, unita="kN"),
        ),
        risultato=puntone.fus_kN, unita="kN", clausola=f"{EC2_PUNTONE}/{EC2_NODO}",
        esito="soddisfatta" if puntone.verificato else "non soddisfatta",
        nota="Verifica \"Puntone\".",
    )


def _passo_alpha(inputs: PlintoSuPaliInput) -> Passo:
    alpha_rad = math.atan(inputs.ly_m / inputs.lx_m)
    return Passo(
        simbolo="α", formula="atan(L_Y / L_X)",
        valori=(
            Valore(simbolo="L_Y", valore=inputs.ly_m, unita="m", descrizione="interasse pali lungo Y"),
            Valore(simbolo="L_X", valore=inputs.lx_m, unita="m", descrizione="interasse pali lungo X"),
        ),
        risultato=alpha_rad, unita="rad",
        nota="Inclinazione della diagonale del gruppo pali; governa la ripartizione della spinta orizzontale "
             "fra i due tiranti ortogonali X e Y (coseno e seno, rispettivamente, per una griglia non quadrata).",
    )


def _passo_check_tirante_xy(puntone: Puntone, tirante: Tirante, fyd_MPa: float) -> Passo:
    formula = f"F_us * {K_TIE_XY_FRACTION:g} * cos(θ) <= A_t,XY * f_yd / 1000"
    valori = (
        Valore(simbolo="F_us", valore=puntone.fus_kN, unita="kN", descrizione="forza nel puntone, calcolata sopra"),
        _valore_theta_rad(puntone),
        Valore(simbolo="A_t,XY", valore=tirante.at_mm2, unita="mm2", descrizione=f"armatura del tirante diagonale XY disposta ({tirante.n_barre}⌀{tirante.diametro_mm:g})"),
        valore_fyd(fyd_MPa),
    )
    return Passo(
        simbolo="F_ut,XY", formula=formula, valori=valori, risultato=tirante.fut_kN, unita="kN", clausola=EC2_TIRANTE,
        esito="soddisfatta" if tirante.verificato else "non soddisfatta",
        nota=f"Verifica \"Tirante XY\"; {K_TIE_XY_FRACTION:g} = quota della spinta orizzontale del puntone assegnata al tirante diagonale.",
    )


def _passo_check_tirante_ortogonale(direzione: str, puntone: Puntone, tirante: Tirante, fyd_MPa: float, alpha_rad: float, funzione: str) -> Passo:
    quota = 1.0 - K_TIE_XY_FRACTION
    formula = f"F_us * cos(θ) * {quota:g} * {funzione}(α) <= A_t,{direzione} * f_yd / 1000"
    valori = (
        Valore(simbolo="F_us", valore=puntone.fus_kN, unita="kN"),
        _valore_theta_rad(puntone),
        Valore(simbolo="α", valore=alpha_rad, unita="rad", descrizione="inclinazione della diagonale del gruppo pali, calcolata sopra"),
        Valore(simbolo=f"A_t,{direzione}", valore=tirante.at_mm2, unita="mm2", descrizione=f"armatura del tirante {direzione} disposta ({tirante.n_barre}⌀{tirante.diametro_mm:g})"),
        valore_fyd(fyd_MPa),
    )
    return Passo(
        simbolo=f"F_ut,{direzione}", formula=formula, valori=valori, risultato=tirante.fut_kN, unita="kN", clausola=EC2_TIRANTE,
        esito="soddisfatta" if tirante.verificato else "non soddisfatta",
        nota=f"Verifica \"Tirante {direzione}\"; cos(θ) proietta la spinta orizzontale del puntone (equilibrio al nodo, EC2 §6.5.3), "
             f"{funzione}(α) ripartisce fra i due tiranti ortogonali su una griglia non quadrata.",
    )


def _passo_check_tirante_fila_singola(direzione: str, puntone: Puntone, tirante: Tirante, fyd_MPa: float) -> Passo:
    formula = f"F_us * cos(θ) <= A_t,{direzione} * f_yd / 1000"
    valori = (
        Valore(simbolo="F_us", valore=puntone.fus_kN, unita="kN", descrizione="forza nel puntone, calcolata sopra"),
        _valore_theta_rad(puntone),
        Valore(simbolo=f"A_t,{direzione}", valore=tirante.at_mm2, unita="mm2", descrizione=f"armatura del tirante disposta ({tirante.n_barre}⌀{tirante.diametro_mm:g})"),
        valore_fyd(fyd_MPa),
    )
    return Passo(
        simbolo=f"F_ut,{direzione}", formula=formula, valori=valori, risultato=tirante.fut_kN, unita="kN", clausola=EC2_TIRANTE,
        esito="soddisfatta" if tirante.verificato else "non soddisfatta",
        nota=f"Verifica \"Tirante {direzione}\"; fila singola di due pali, l'intera spinta orizzontale del puntone è assegnata al tirante.",
    )


def _passo_utilizzo_st(output: PlintoSuPaliOutput, pt: PuntoniTiranti) -> Passo:
    valori = [Valore(simbolo="η_puntone", valore=pt.puntone.utilizzo, unita="-", descrizione="utilizzo del puntone, calcolato sopra")]
    for nome, tirante in (("XY", pt.tirante_xy), ("X", pt.tirante_x), ("Y", pt.tirante_y)):
        if tirante is not None:
            valori.append(Valore(simbolo=f"η_tirante,{nome}", valore=tirante.utilizzo, unita="-", descrizione=f"utilizzo del tirante {nome}, calcolato sopra"))
    formula = "max(" + ", ".join(v.simbolo for v in valori) + ")"
    return Passo(
        simbolo="η_st", formula=formula, valori=tuple(valori), risultato=output.utilizzo_puntoni_tiranti, unita="-",
        nota="Utilizzo governante fra puntone e tiranti (indicatore di sintesi, non un Check autonomo).",
    )

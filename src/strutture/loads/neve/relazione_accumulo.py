"""Verified restatement (docs/architecture-phase2.md §6) of `neve-accumulo`'s drift-geometry and
design steps: drift-zone length l_s (`accumulo_ls.py`, EN 1991-1-3 Allegato B.3), wind-redistribution
shape coefficient μ_w (`accumulo_mw.py`, Circ. NTC2018 §C3.4.5.6 mirroring EN 1991-1-3 §6.2(3)),
sliding shape coefficient μ_s (`accumulo_ms.py`), the design shape coefficient at the far edge μ_1,
final (`accumulo_m1.py`) and the two design snow loads q_s1/q_s2 (NTC2018 §3.4.1 eq. 3.4.1). The
calculation code is never touched: `γh/q_sk` (`accumulo_mw.py::rapporto_gamma_h_qsk`) is not exposed
by `AccumuloOutput`, so its formula is restated inline inside the μ_w passo (the same reuse-a-formula-
fragment technique `ca_travi/relazione_taglio.py::_sin2_theta_formula` uses), never re-derived by
hand.

Clause label "Circ. NTC2018 §C3.4.5.6" matches this tool's own registered `Tool.norm`
(`tool.py::TOOLS`) verbatim, even though the explanatory circular it refers to was itself published
in 2019 (`accumulo_mw.py`'s own docstring says "Circ. 2019 §C3.4.5.6") — the pre-existing codebase
is not fully consistent on the circular's year, and the trace follows the tool's own registered
citation rather than introduce a THIRD spelling."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .accumulo_ls import LS_MAX_M, LS_MIN_M
from .accumulo_m1 import M1_INTERP_MAX, M1_INTERP_MIN
from .accumulo_ms import SLIDE_ANGLE_THRESHOLD_DEG
from .accumulo_mw import MW_MAX, MW_MIN
from .models import AccumuloInput, AccumuloOutput

CLAUSOLA_LS = "EN 1991-1-3 Allegato B.3"
CLAUSOLA_MW = "Circ. NTC2018 §C3.4.5.6 / EN 1991-1-3 §6.2(3)"
CLAUSOLA_MS = "Circ. NTC2018 §C3.4.5.6 / EN 1991-1-3 Allegato B.3"
CLAUSOLA_ACCUMULO = "Circ. NTC2018 §C3.4.5.6"
CLAUSOLA_QS = "NTC2018 §3.4.1 eq. (3.4.1)"


def traccia_lunghezza_e_coefficienti(inputs: AccumuloInput, output: AccumuloOutput) -> Traccia:
    """4 passi: l_s, μ_w, μ_s, μ_2 = μ_s + μ_w."""
    return Traccia(
        titolo="Lunghezza e coefficienti di forma della zona di accumulo",
        passi=(_passo_ls(inputs, output), _passo_mw(inputs, output), _passo_ms(inputs, output), _passo_m2(output)),
    )


def traccia_progetto(inputs: AccumuloInput, output: AccumuloOutput) -> Traccia:
    """3 passi: μ_1,final (interpolato o imposto), q_s1 e q_s2 di progetto."""
    return Traccia(
        titolo="Coefficiente di forma di progetto e carichi neve di accumulo",
        passi=(
            _passo_m1_final(inputs, output),
            _passo_qs_finale("q_s1", "μ_1,final", output.m1_final, inputs.ct, output, output.qs1_final),
            _passo_qs_finale("q_s2", "μ_2", output.m2_final, inputs.ct, output, output.qs2_final),
        ),
    )


def _passo_ls(inputs: AccumuloInput, output: AccumuloOutput) -> Passo:
    return Passo(
        simbolo="l_s",
        formula="min(max(2 * h, l_s,min), l_s,max)",
        valori=(
            Valore(simbolo="h", valore=inputs.h, unita="m", descrizione="dislivello tra le due coperture"),
            Valore(simbolo="l_s,min", valore=LS_MIN_M, unita="m", descrizione="lunghezza minima"),
            Valore(simbolo="l_s,max", valore=LS_MAX_M, unita="m", descrizione="lunghezza massima"),
        ),
        risultato=output.ls, unita="m", clausola=CLAUSOLA_LS,
        nota=f"Lunghezza della zona di accumulo, l_s=2h limitata all'intervallo [{LS_MIN_M:g}; {LS_MAX_M:g}] m.",
    )


def _passo_mw(inputs: AccumuloInput, output: AccumuloOutput) -> Passo:
    return Passo(
        simbolo="μ_w",
        formula="min(μ_w,max, max(μ_w,min, min((b_1 + b_2) / (2 * h), γ * h / q_sk)))",
        valori=(
            Valore(simbolo="b_1", valore=inputs.b1, unita="m", descrizione="larghezza della costruzione più alta"),
            Valore(simbolo="b_2", valore=inputs.b2, unita="m", descrizione="larghezza della costruzione più bassa"),
            Valore(simbolo="h", valore=inputs.h, unita="m", descrizione="dislivello tra le due coperture"),
            Valore(simbolo="γ", valore=inputs.gamma, unita="kN/m³", descrizione="peso specifico della neve"),
            Valore(simbolo="q_sk", valore=output.qsk, unita="kN/m²", descrizione="carico neve al suolo, calcolato sopra"),
            Valore(simbolo="μ_w,min", valore=MW_MIN, descrizione="limite inferiore del coefficiente"),
            Valore(simbolo="μ_w,max", valore=MW_MAX, descrizione="limite superiore del coefficiente"),
        ),
        risultato=output.mw, unita="-", clausola=CLAUSOLA_MW,
        nota="Coefficiente di forma da ridistribuzione del vento: minimo tra il rapporto geometrico "
             f"(b_1+b_2)/(2h) e γh/q_sk, limitato all'intervallo [{MW_MIN:g}; {MW_MAX:g}].",
    )


def _passo_ms(inputs: AccumuloInput, output: AccumuloOutput) -> Passo:
    # La condizione sull'angolo va nel simbolo stampato, non solo nella nota (`traccia_a_testo`
    # non stampa mai `Passo.nota`, review finding MISSING_STEP): altrimenti "μ_s = 0" si legge
    # come una legge incondizionata, non come l'esito del solo ramo α < 15°.
    if inputs.a < SLIDE_ANGLE_THRESHOLD_DEG:
        return Passo(
            simbolo=f"μ_s  (α < {SLIDE_ANGLE_THRESHOLD_DEG:g}°)", formula="0", valori=(),
            risultato=output.ms, unita="-", clausola=CLAUSOLA_MS,
            nota=f"Angolo della falda più alta α={inputs.a:g}° < {SLIDE_ANGLE_THRESHOLD_DEG:g}°: "
                 "nessun contributo da scivolamento.",
        )
    return Passo(
        simbolo=f"μ_s  (α ≥ {SLIDE_ANGLE_THRESHOLD_DEG:g}°)",
        formula="μ_sup / 2",
        valori=(Valore(simbolo="μ_sup", valore=inputs.msup, descrizione="coefficiente di forma della falda superiore"),),
        risultato=output.ms, unita="-", clausola=CLAUSOLA_MS,
        nota=f"Angolo della falda più alta α={inputs.a:g}° ≥ {SLIDE_ANGLE_THRESHOLD_DEG:g}°: metà del "
             "coefficiente di forma della falda superiore.",
    )


def _passo_m2(output: AccumuloOutput) -> Passo:
    return Passo(
        simbolo="μ_2",
        formula="μ_s + μ_w",
        valori=(
            Valore(simbolo="μ_s", valore=output.ms, descrizione="coefficiente da scivolamento, calcolato sopra"),
            Valore(simbolo="μ_w", valore=output.mw, descrizione="coefficiente da ridistribuzione del vento, calcolato sopra"),
        ),
        risultato=output.m2, unita="-", clausola=CLAUSOLA_ACCUMULO,
        nota="Coefficiente di forma totale al muro della costruzione più alta.",
    )


def _passo_m1_final(inputs: AccumuloInput, output: AccumuloOutput) -> Passo:
    if inputs.b2 < output.ls:
        return Passo(
            simbolo="μ_1,final",
            formula="min(max((μ_w - μ_1,imp) / l_s * (l_s - b_2) + μ_1,imp, μ_1,inf), μ_1,sup)",
            valori=(
                Valore(simbolo="μ_w", valore=output.mw, descrizione="coefficiente al muro, calcolato sopra"),
                Valore(simbolo="μ_1,imp", valore=inputs.m1_input,
                       descrizione="coefficiente di forma imposto per il bordo lontano dalla costruzione più alta"),
                Valore(simbolo="l_s", valore=output.ls, unita="m", descrizione="lunghezza della zona di accumulo, calcolata sopra"),
                Valore(simbolo="b_2", valore=inputs.b2, unita="m", descrizione="larghezza della costruzione più bassa"),
                Valore(simbolo="μ_1,inf", valore=M1_INTERP_MIN, descrizione="limite inferiore dell'interpolazione"),
                Valore(simbolo="μ_1,sup", valore=M1_INTERP_MAX,
                       descrizione="limite superiore dell'interpolazione, pari al limite superiore di μ_w"),
            ),
            risultato=output.m1_final, unita="-", clausola=CLAUSOLA_ACCUMULO,
            nota=f"Costruzione più bassa più stretta della zona di accumulo (b_2={inputs.b2:g} m < "
                 f"l_s={output.ls:g} m): μ_1 è interpolato linearmente tra μ_w (al muro) e μ_1,imp (al bordo lontano).",
        )
    return Passo(
        simbolo="μ_1,final",
        formula="μ_1,imp",
        valori=(
            Valore(simbolo="μ_1,imp", valore=inputs.m1_input,
                   descrizione="coefficiente di forma imposto per il bordo lontano dalla costruzione più alta"),
        ),
        risultato=output.m1_final, unita="-", clausola=CLAUSOLA_ACCUMULO,
        nota=f"Costruzione più bassa non più stretta della zona di accumulo (b_2={inputs.b2:g} m ≥ "
             f"l_s={output.ls:g} m): resta il valore imposto in ingresso.",
    )


def _passo_qs_finale(simbolo: str, simbolo_mu: str, mu_val: float, ct_val: float, output: AccumuloOutput, risultato: float) -> Passo:
    return Passo(
        simbolo=simbolo,
        formula=f"q_sk * C_E * C_t * {simbolo_mu}",
        valori=(
            Valore(simbolo="q_sk", valore=output.qsk, unita="kN/m²", descrizione="carico neve al suolo, calcolato sopra"),
            Valore(simbolo="C_E", valore=output.ce, descrizione="coefficiente di esposizione, calcolato sopra"),
            Valore(simbolo="C_t", valore=ct_val, descrizione="coefficiente termico, calcolato sopra"),
            Valore(simbolo=simbolo_mu, valore=mu_val, descrizione="coefficiente di forma di progetto, calcolato sopra"),
        ),
        risultato=risultato, unita="kN/m²", clausola=CLAUSOLA_QS,
        nota="Carico neve di progetto di accumulo.",
    )

"""Verified restatement (docs/architecture-phase2.md) of `critica_elastica.py` (N_cr,yy/N_cr,zz)
and `instabilita_flessionale.py` (λ̄_yy/λ̄_zz, χ_yy/χ_zz — EN1993-1-1 §6.3.1.2 eq. 6.49/6.50); Φ is
folded into χ's own formula (used only there, never on its own, mirroring
`ca_travi.relazione_taglio`'s inline `sin²θ` sub-expression) rather than given its own `Passo`.

λ̄_yy/λ̄_zz use the CHARACTERISTIC f_yk (`instabilita_flessionale.py`'s own fixed-mode behaviour,
N_Rk=A·f_yk per eq. 6.50 — the legacy sheet uses f_yd instead, a divergence already fixed and
documented there, not repeated here). α_yy/α_zz (Tab. 6.1) and the buckling curve letter (Tab. 6.2,
selected from h/b, t_f, steel grade and rolled/welded — `Sezione`'s own logic, never re-derived) each
get their own "lookup only" `Passo` (review finding MISSING_STEP: they used to be bare literals
inside χ's own formula, unlike every table value in the loads packages, which gets a `Passo`):
neither χ_yy nor χ_zz feeds a `Check` of its own (this package has no standalone N_b,Rd check) —
both are informative, feeding the interaction of `relazione_interazione.py` (§6.3.3) only, and say
so in their `nota`.
"""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .relazione_comune import KN_A_N, N_A_KN
from .results import ColonnaEc3Output

_TABELLA_CURVE = "EN1993-1-1 Tab. 6.1 (α) / Tab. 6.2 (curva, sezioni H/I laminate)"


def traccia_instabilita_flessionale(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """8 passi: N_cr,yy, N_cr,zz, λ̄_yy, λ̄_zz, α_yy, α_zz, χ_yy, χ_zz."""
    return Traccia(
        titolo="Instabilità per flessione semplice",
        passi=(
            _passo_ncr(inputs, output, "yy"), _passo_ncr(inputs, output, "zz"),
            _passo_lambda(inputs, output, "yy"), _passo_lambda(inputs, output, "zz"),
            _passo_alpha(output, "yy"), _passo_alpha(output, "zz"),
            _passo_chi(output, "yy"), _passo_chi(output, "zz"),
        ),
    )


def _passo_alpha(output: ColonnaEc3Output, asse: str) -> Passo:
    simbolo = f"α_{asse}"
    valore = output.sezione.alpha_yy if asse == "yy" else output.sezione.alpha_zz
    curva = output.sezione.curva_flessionale_yy if asse == "yy" else output.sezione.curva_flessionale_zz
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione=f"fattore di imperfezione, curva {curva!r}"),),
        risultato=valore, unita="-", clausola=_TABELLA_CURVE,
        nota=f"Curva di instabilità {curva!r} selezionata da h/b, t_f, grado dell'acciaio e "
             "laminata/saldata (sezione.py); il fattore di imperfezione α è tabellare, Tab. 6.1.",
    )


def _passo_ncr(inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str) -> Passo:
    inerzia_simbolo = "I_yy" if asse == "yy" else "I_zz"
    inerzia = inputs.iyy_mm4 if asse == "yy" else inputs.izz_mm4
    lcr_simbolo = f"L_cr,{asse}"
    lcr = inputs.lcr_yy_mm if asse == "yy" else inputs.lcr_zz_mm
    risultato = output.instabilita_flessionale.ncr_y_kN if asse == "yy" else output.instabilita_flessionale.ncr_z_kN
    return Passo(
        simbolo=f"N_cr,{asse}",
        formula=f"π^2 * E * {inerzia_simbolo} / {lcr_simbolo}^2",
        valori=(
            Valore(simbolo="π", valore=math.pi),
            Valore(simbolo="E", valore=inputs.e_MPa, unita="MPa", descrizione="modulo elastico dell'acciaio"),
            Valore(simbolo=inerzia_simbolo, valore=inerzia, unita="mm4"),
            Valore(simbolo=lcr_simbolo, valore=lcr, unita="mm", descrizione="lunghezza libera di inflessione"),
        ),
        risultato=risultato, unita="kN", scala=N_A_KN, clausola="EN1993-1-1 §6.3.1.2 (nota sotto eq. 6.50)",
        nota="Carico critico euleriano a flessione, sezione lorda.",
    )


def _passo_lambda(inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str) -> Passo:
    ncr_simbolo = f"N_cr,{asse}"
    ncr = output.instabilita_flessionale.ncr_y_kN if asse == "yy" else output.instabilita_flessionale.ncr_z_kN
    risultato = output.instabilita_flessionale.lambda_yy if asse == "yy" else output.instabilita_flessionale.lambda_zz
    return Passo(
        simbolo=f"λ_{asse}",
        formula=f"sqrt(A * f_yk / ({ncr_simbolo} * {KN_A_N:g}))",
        valori=(
            Valore(simbolo="A", valore=inputs.area_mm2, unita="mm2"),
            Valore(simbolo="f_yk", valore=output.materiali.fyk_MPa, unita="MPa"),
            Valore(simbolo=ncr_simbolo, valore=ncr, unita="kN", descrizione="calcolato sopra"),
        ),
        risultato=risultato, unita="-", clausola="EN1993-1-1 §6.3.1.2 eq. (6.50)",
        nota="Snellezza adimensionale: l'eq. (6.50) impiega la resistenza CARATTERISTICA f_yk "
             "(N_Rk=A·f_yk), non f_yd.",
    )


def _passo_chi(output: ColonnaEc3Output, asse: str) -> Passo:
    lam = f"λ_{asse}"
    alpha = f"α_{asse}"
    fi = f"(0.5*(1+{alpha}*({lam}-0.2)+{lam}^2))"
    lambda_val = output.instabilita_flessionale.lambda_yy if asse == "yy" else output.instabilita_flessionale.lambda_zz
    alpha_val = output.sezione.alpha_yy if asse == "yy" else output.sezione.alpha_zz
    risultato = output.instabilita_flessionale.chi_yy if asse == "yy" else output.instabilita_flessionale.chi_zz
    return Passo(
        simbolo=f"χ_{asse}",
        formula=f"min(1, 1/({fi} + sqrt({fi}^2-{lam}^2)))",
        valori=(
            Valore(simbolo=alpha, valore=alpha_val, descrizione="calcolato sopra"),
            Valore(simbolo=lam, valore=lambda_val, descrizione="calcolato sopra"),
        ),
        risultato=risultato, unita="-", clausola="EN1993-1-1 §6.3.1.2 eq. (6.49)",
        nota="Fattore riduttivo per instabilità flessionale. Non è una verifica a sé stante: alimenta "
             "l'interazione N-My-Mz (§6.3.3).",
    )

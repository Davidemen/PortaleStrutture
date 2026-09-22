"""Verified restatement (docs/architecture-phase2.md) of `snellezza.py` (NTC2018 §4.1.2.3.9.2,
λ_lim = 15.4·C/√n) and `limiti_ec2.py` (EC2 §5.8.3.1(1), λ_lim = 20·A·B·C/√n). Which formula applies
follows `inputs.norma` through `regole.resolve` (architecture-batch2.md §3; `legacy_compat=False`
throughout, `relazione` never runs in Excel mode). `A`, `B`, `C` and `n` are named, described
`Valore`s of the SAME `λ_lim` step rather than separate `Passo`s of their own (docs/architecture-
phase2.md lesson: "a coefficient... gets a step OR a named Valore with a descrizione"), since none
of the four is reused outside this one formula — this keeps the package's per-tool step count
inside the 10-30 target while still surfacing every coefficient by name. `i` (radius of gyration)
and `l_0` (buckling length) are likewise named `Valore`s of `λ` rather than of their own `Passo`s."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import kn_to_n

from . import limiti_ec2
from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .regole import resolve
from .snellezza import LAMBDA_LIM_COEFFICIENT

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput

_C_DESCRIZIONE = (
    "C = 1,7 - r_m (rapporto fra i momenti alle estremità); r_m assunto pari a 1 (singola "
    "curvatura) se non noto, da cui C=0,7"
)


def traccia_snellezza_rettangolare(inputs: PilastroRettangolareInput, output: PilastroOutput) -> Traccia:
    """CALCULATION FINDING: `i` usa sempre L_2 (i = L_2/√12, sezione lorda), MAI il lato minore fra
    L_1 e L_2 — `snellezza.raggio_inerzia_netto_rettangolare_mm` (ramo netto, non usato in modalità
    standard) prende correttamente `min(L_1, L_2)`/`max(L_1, L_2)`, ma il ramo lordo qui attivo
    (`shared.section_geometry.rect(inputs.l1_mm, inputs.l2_mm)`) no: per una sezione con L_1 < L_2
    la snellezza calcolata sarebbe NON conservativa (i sovrastimato, λ sottostimato) perché l'asse
    debole (quello governato da L_1) non è mai verificato quando L_1 è il lato passato per primo ma
    è più corto di L_2. Non corretto qui (la formula del codice non cambia): restiamo fedeli a
    quanto calcola `tool_rettangolare.py`."""
    i_mm = output.snellezza.i_mm
    valore_i = Valore(
        simbolo="i", valore=i_mm, unita="mm",
        descrizione="raggio d'inerzia, i = L_2/√12 (sezione lorda) — SEMPRE su L_2, indipendentemente da quale "
                     "lato sia il più corto (vedi nota del passo λ)",
    )
    nota_lambda = (
        "Snellezza del pilastro. Nota di calcolo: i è calcolato solo su L_2 (i = L_2/√12), mai sul lato minore "
        "fra L_1 e L_2: per una sezione con L_1 < L_2 la snellezza sull'asse debole (quello governato da L_1) "
        "non è verificata da questo calcolo, che resta quindi potenzialmente non conservativo per sezioni non "
        "quadrate — il codice non è stato modificato qui."
    )
    return _traccia_snellezza(inputs, output, valore_i, nota_lambda)


def traccia_snellezza_circolare(inputs: PilastroCircolareInput, output: PilastroOutput) -> Traccia:
    i_mm = output.snellezza.i_mm
    valore_i = Valore(simbolo="i", valore=i_mm, unita="mm", descrizione="raggio d'inerzia, i = D/4 (sezione lorda)")
    return _traccia_snellezza(inputs, output, valore_i, "Snellezza del pilastro.")


def _traccia_snellezza(inputs: PilastroInput, output: PilastroOutput, valore_i: Valore, nota_lambda: str) -> Traccia:
    """3 passi: λ_lim, λ, Check "Verifica di snellezza"."""
    rules = resolve(inputs.norma, legacy_compat=False)
    snellezza, geometria, materiali = output.snellezza, output.geometria, output.materiali
    n_val = kn_to_n(inputs.ned_kN) / (geometria.ac_mm2 * materiali.fcd_MPa)
    valore_n = Valore(simbolo="n", valore=n_val, descrizione="n = N_Ed·1000/(A_c·f_cd)")
    valore_c = Valore(simbolo="C", valore=output.regole.c_snellezza, descrizione=_C_DESCRIZIONE)

    if rules.lambda_lim_kind == "ec2":
        passo_lambda_lim = _passo_lambda_lim_ec2(inputs, output, valore_n, valore_c)
    else:
        passo_lambda_lim = _passo_lambda_lim_ntc(valore_n, valore_c, snellezza.lambda_lim)

    valore_l0 = Valore(
        simbolo="l_0", valore=snellezza.l0_mm, unita="mm",
        descrizione="lunghezza libera di inflessione: l_0 se specificata in input, altrimenti l'altezza netta H",
    )
    passo_lambda = Passo(
        simbolo="λ", formula="l_0 / i", valori=(valore_l0, valore_i),
        risultato=snellezza.lambda_, unita="-", clausola="NTC2018 §4.1.2.3.9.2 / EC2 §5.8.3.1",
        nota=nota_lambda,
    )
    soddisfatta = snellezza.lambda_ < snellezza.lambda_lim
    passo_check = Passo(
        simbolo="λ/λ_lim", formula="λ < λ_lim",
        valori=(
            Valore(simbolo="λ", valore=snellezza.lambda_, descrizione="calcolata sopra"),
            Valore(simbolo="λ_lim", valore=snellezza.lambda_lim, descrizione="calcolata sopra"),
        ),
        risultato=snellezza.lambda_, unita="-", clausola="NTC2018 §4.1.2.3.9.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta", nota="Verifica di snellezza.",
    )
    return Traccia(titolo="Snellezza", passi=(passo_lambda_lim, passo_lambda, passo_check))


def _passo_lambda_lim_ntc(valore_n: Valore, valore_c: Valore, lambda_lim: float) -> Passo:
    return Passo(
        simbolo="λ_lim", formula=f"{LAMBDA_LIM_COEFFICIENT:g} * C / sqrt(n)",
        valori=(valore_c, valore_n),
        risultato=lambda_lim, unita="-", clausola="NTC2018 §4.1.2.3.9.2",
        nota=f"Coefficiente {LAMBDA_LIM_COEFFICIENT:g} secondo NTC2018 §4.1.2.3.9.2 (≈20·A·B con A=0,7 e B=1,1, valori tipici).",
    )


def _passo_lambda_lim_ec2(inputs: PilastroInput, output: PilastroOutput, valore_n: Valore, valore_c: Valore) -> Passo:
    omega = output.regole.omega_meccanico
    b_val = math.sqrt(1.0 + 2.0 * omega)
    a_descrizione = (
        f"A = 1/(1+0,2·φ_ef), φ_ef={inputs.phi_ef:g} (in input)"
        if inputs.phi_ef is not None
        else f"φ_ef non noto: A assunto pari a {limiti_ec2.A_DEFAULT:g} (EC2 §5.8.3.1(1) nota 1)"
    )
    valore_a = Valore(simbolo="A", valore=output.regole.a_snellezza, descrizione=a_descrizione)
    valore_b = Valore(simbolo="B", valore=b_val, descrizione=f"B = √(1+2·ω), ω=rapporto meccanico di armatura={omega:.4g}")
    return Passo(
        simbolo="λ_lim", formula=f"{limiti_ec2.LAMBDA_LIM_COEFFICIENT_EC2:g} * A * B * C / sqrt(n)",
        valori=(valore_a, valore_b, valore_c, valore_n),
        risultato=output.snellezza.lambda_lim, unita="-", clausola="EC2 §5.8.3.1(1)",
        nota="Snellezza limite EC2, coefficienti A/B/C/n secondo la nota 1 e la nota 3 del §5.8.3.1(1).",
    )

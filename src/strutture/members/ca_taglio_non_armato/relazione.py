"""Verified restatement of the ca-taglio-non-armato formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md, NTC2018 §4.1.2.3.5.1 / EN1992-1-1 §6.2.2). Pure function of the
tool's own validated inputs and already-computed output; the calculation code of this package is
never touched. `rho_l_raw` — the pre-cap ratio the §4.1.2.3.5.1 limit is actually checked against
— is not exposed by `TaglioOutput`, so it is read straight from the package's own step function
(`longitudinal_ratio.rho_l_raw`), exactly as the architecture brief allows.

Notation identifiers must be grammar-legal (`shared.relazione.notazione`): the UI symbol hints "N°"
and "⌀" are not (a degree sign and a diameter sign are not letters), so the bar-count/diameter
formula below uses "n" and "φ" instead, with a `descrizione` naming the field they stand for.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .longitudinal_ratio import rho_l_raw
from .models import TaglioNonArmatoInput, TaglioNonArmatoOutput
from .tables import (
    ALPHA_CC,
    FCK_FROM_RCK_FACTOR,
    RHO_L_MAX,
    SIGMA_CP_MAX_FACTOR,
    VMIN_COEFF,
    VRD1_COEFF,
    VRD1_SIGMA_CP_COEFF,
    VRD2_SIGMA_CP_COEFF,
)

PI_GRECO = 3.141592653589793
KN_TO_N = 1000.0  # sheet/kn_to_n conversion, embedded as a formula literal (N_Ed is given in kN)
SCALA_N_A_KN = 0.001  # display factor for the shear-resistance terms, computed in N


def relazione(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> tuple[Traccia, ...]:
    """8-25 steps (here 10) covering the one code Check (rapporto di armatura longitudinale) and
    the one highlighted output (V_Rd)."""
    return (
        _traccia_materiali(inputs, output),
        _traccia_geometria(inputs, output),
        _traccia_resistenza_a_taglio(inputs, output),
    )


def _traccia_materiali(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Traccia:
    passi = (_passo_fck(inputs, output),) if inputs.fck_MPa is None else ()
    return Traccia(titolo="Materiali", passi=(*passi, _passo_fcd(inputs, output)))


def _passo_fck(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="f_ck",
        formula=f"{FCK_FROM_RCK_FACTOR} * R_ck",
        valori=(Valore(simbolo="R_ck", valore=inputs.rck_MPa, unita="MPa", descrizione="resistenza cubica caratteristica"),),
        risultato=output.materiali.fck_MPa, unita="MPa", clausola="NTC2018 §11.2.10.1",
        nota="fck = 0,83·Rck in assenza di un valore diretto.",
    )


def _passo_fcd(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="f_cd",
        formula=f"{ALPHA_CC} * f_ck / γ_c",
        valori=(
            Valore(simbolo="f_ck", valore=output.materiali.fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica"),
            Valore(simbolo="γ_c", valore=inputs.gamma_c, descrizione="coefficiente parziale del calcestruzzo"),
        ),
        risultato=output.materiali.fcd_MPa, unita="MPa", clausola="NTC2018 §4.1.2.1.1.1",
    )


def _traccia_geometria(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Traccia:
    passi = (_passo_d(inputs, output),)
    if inputs.n_barre is not None and inputs.diametro_barre_mm is not None:
        passi = (*passi, _passo_asl_da_barre(inputs, output))
    return Traccia(titolo="Geometria della sezione", passi=passi)


def _passo_d(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="d",
        formula="h - c",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="c", valore=inputs.c_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=output.geometria.d_mm, unita="mm",
    )


def _passo_asl_da_barre(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="A_sl",
        formula="n * π * φ^2 / 4",
        valori=(
            Valore(simbolo="n", valore=float(inputs.n_barre), descrizione="numero di barre (N° in input)"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ", valore=inputs.diametro_barre_mm, unita="mm", descrizione="diametro delle barre (⌀ in input)"),
        ),
        risultato=output.geometria.asl_mm2, unita="mm2",
    )


def _traccia_resistenza_a_taglio(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Traccia:
    passi = (
        _passo_sigma_cp(inputs, output),
        _passo_k(output),
        _passo_vmin(output),
        _passo_verifica_rho_l(inputs, output),
        _passo_vrd1(output, inputs),
        _passo_vrd2(output, inputs),
        _passo_vrd(output),
    )
    return Traccia(titolo="Resistenza a taglio (NTC2018 §4.1.2.3.5.1)", passi=passi)


def _passo_sigma_cp(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="σ_cp",
        formula=f"min({KN_TO_N:g} * N_Ed / (b_w * h), {SIGMA_CP_MAX_FACTOR} * f_cd)",
        valori=(
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN", descrizione="azione assiale, positiva se di compressione"),
            Valore(simbolo="b_w", valore=inputs.bw_mm, unita="mm"),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="f_cd", valore=output.materiali.fcd_MPa, unita="MPa"),
        ),
        risultato=output.taglio.sigma_cp_MPa, unita="MPa", clausola="NTC2018 §4.1.2.3.5.1",
        nota="Tensione media di compressione, limitata a 0,2·fcd.",
    )


def _passo_k(output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="k",
        formula="min(1 + sqrt(200 / d), 2)",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=output.taglio.k, unita="-", clausola="NTC2018 §4.1.2.3.5.1",
        nota="Fattore di scala per l'effetto dimensionale.",
    )


def _passo_vmin(output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="v_min",
        formula=f"{VMIN_COEFF} * k^1.5 * sqrt(f_ck)",
        valori=(
            Valore(simbolo="k", valore=output.taglio.k),
            Valore(simbolo="f_ck", valore=output.materiali.fck_MPa, unita="MPa"),
        ),
        risultato=output.taglio.vmin_MPa, unita="MPa", clausola="NTC2018 §4.1.2.3.5.1",
    )


def _passo_verifica_rho_l(inputs: TaglioNonArmatoInput, output: TaglioNonArmatoOutput) -> Passo:
    raw = rho_l_raw(output.geometria.asl_mm2, inputs.bw_mm, output.geometria.d_mm)
    soddisfatta = raw <= RHO_L_MAX
    return Passo(
        simbolo="ρ_l",
        formula=f"A_sl / (b_w * d) <= {RHO_L_MAX}",
        valori=(
            Valore(simbolo="A_sl", valore=output.geometria.asl_mm2, unita="mm2"),
            Valore(simbolo="b_w", valore=inputs.bw_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=raw, unita="-", clausola="NTC2018 §4.1.2.3.5.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Rapporto geometrico di armatura longitudinale tesa, limitato a ρl,max nel calcolo di VRd,1.",
    )


def _passo_vrd1(output: TaglioNonArmatoOutput, inputs: TaglioNonArmatoInput) -> Passo:
    return Passo(
        simbolo="V_Rd,1",
        formula=f"({VRD1_COEFF} * k * (100 * ρ_l * f_ck)^(1/3) / γ_c + {VRD1_SIGMA_CP_COEFF} * σ_cp) * b_w * d",
        valori=(
            Valore(simbolo="k", valore=output.taglio.k),
            Valore(simbolo="ρ_l", valore=output.taglio.rho_l, descrizione="rapporto di armatura, già limitato a ρl,max"),
            Valore(simbolo="f_ck", valore=output.materiali.fck_MPa, unita="MPa"),
            Valore(simbolo="γ_c", valore=inputs.gamma_c),
            Valore(simbolo="σ_cp", valore=output.taglio.sigma_cp_MPa, unita="MPa"),
            Valore(simbolo="b_w", valore=inputs.bw_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.taglio.vrd1_kN, unita="kN", scala=SCALA_N_A_KN, clausola="NTC2018 §4.1.2.3.5.1",
        nota="Termine con il contributo dell'armatura longitudinale.",
    )


def _passo_vrd2(output: TaglioNonArmatoOutput, inputs: TaglioNonArmatoInput) -> Passo:
    return Passo(
        simbolo="V_Rd,2",
        formula=f"(v_min + {VRD2_SIGMA_CP_COEFF} * σ_cp) * b_w * d",
        valori=(
            Valore(simbolo="v_min", valore=output.taglio.vmin_MPa, unita="MPa"),
            Valore(simbolo="σ_cp", valore=output.taglio.sigma_cp_MPa, unita="MPa"),
            Valore(simbolo="b_w", valore=inputs.bw_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.taglio.vrd2_kN, unita="kN", scala=SCALA_N_A_KN, clausola="NTC2018 §4.1.2.3.5.1",
        nota="Termine di resistenza minima.",
    )


def _passo_vrd(output: TaglioNonArmatoOutput) -> Passo:
    return Passo(
        simbolo="V_Rd",
        formula="max(V_Rd,1, V_Rd,2)",
        valori=(
            Valore(simbolo="V_Rd,1", valore=output.taglio.vrd1_kN, unita="kN"),
            Valore(simbolo="V_Rd,2", valore=output.taglio.vrd2_kN, unita="kN"),
        ),
        risultato=output.taglio.vrd_kN, unita="kN", clausola="NTC2018 §4.1.2.3.5.1",
        nota="Resistenza a taglio di calcolo della sezione priva di armatura trasversale.",
    )

"""Traccia "Geometria e verifica al filo del pilastro": effective depth, control perimeter u0 and
the punching-shear check at the column face (EN 1992-1-1 §6.4.3(1)/§6.4.5(3)), the first section of
`relazione.py` (docs/architecture-phase2.md §6)."""
from strutture.shared.ec2_shear.v_rd_max import FCK_LIMIT_FOR_NU, NU_COEFFICIENT
from strutture.shared.materials.concrete import ALPHA_CC
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import PunzonamentoInput, PunzonamentoOutput
from .relazione_comune import (
    GAMMA_C,
    KN_TO_N,
    RIDUZIONE_TERRENO_CLAUSE,
    SCALA_N_A_KN,
    formula_area_colonna,
    formula_perimetro,
    valori_colonna,
    valori_pi_se_circolare,
)

FACCIA_CLAUSE = "EN 1992-1-1 §6.4.5(3)"
D_EFFICACE_CLAUSE = "EN 1992-1-1 §6.4.2(1)"  # d_x/d: altezza utile media (eq. 6.32) — NON §6.4.4(1),
# che è la formula di v_Rd,c/rho_l (review finding, WRONG_CLAUSE).
K_MAX_DESCRIZIONE = (
    "coefficiente di v_Rd,max = k_max·ν·fcd: 0,4 (EN 1992-1-1/A1:2014, valore raccomandato) oppure "
    "0,5 (EN 1992-1-1:2004 con Appendice Nazionale italiana) — rinominato da 'c' per non collidere "
    "col copriferro (review finding, MISLEADING)"
)


def traccia_faccia_pilastro(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float) -> Traccia:
    passi = (
        _passo_beta(inputs, beta),
        _passo_dx(inputs, output),
        _passo_dy(inputs, output),
        _passo_d(output),
        _passo_u0(inputs, output),
        _passo_ved_red_0(inputs, output, beta),
        _passo_ved_0(output),
        _passo_vrd_max(inputs, output),
        _passo_check_filo_pilastro(output),
    )
    return Traccia(titolo="Geometria e verifica al filo del pilastro", passi=passi)


def _passo_beta(inputs: PunzonamentoInput, beta: float) -> Passo:
    return Passo(
        simbolo="β", formula=f"{beta:g}", valori=(), risultato=beta, unita="-",
        clausola="EN 1992-1-1 §6.4.3(6)",
        nota=f"Fattore di eccentricità da fig. 6.21N, per pilastro '{inputs.posizione}'.",
    )


def _passo_dx(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="d_x", formula="H - c - φ_x / 2",
        valori=(
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="spessore del solaio/platea"),
            Valore(simbolo="c", valore=inputs.copriferro_mm, unita="mm", descrizione="copriferro"),
            Valore(simbolo="φ_x", valore=inputs.phix_mm, unita="mm", descrizione="diametro delle armature tese in direzione x"),
        ),
        risultato=output.geometria.dx_mm, unita="mm", clausola=D_EFFICACE_CLAUSE,
        nota="Altezza utile in direzione x.",
    )


def _passo_dy(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="d_y", formula="d_x - (φ_x + φ_y) / 2",
        valori=(
            Valore(simbolo="d_x", valore=output.geometria.dx_mm, unita="mm"),
            Valore(simbolo="φ_x", valore=inputs.phix_mm, unita="mm"),
            Valore(simbolo="φ_y", valore=inputs.phiy_mm, unita="mm", descrizione="diametro delle armature tese in direzione y"),
        ),
        risultato=output.geometria.dy_mm, unita="mm",
        nota="La seconda cortina di barre parte oltre l'intero diametro φ_x della prima (d_y annidata su d_x).",
    )


def _passo_d(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="d", formula="(d_x + d_y) / 2",
        valori=(
            Valore(simbolo="d_x", valore=output.geometria.dx_mm, unita="mm"),
            Valore(simbolo="d_y", valore=output.geometria.dy_mm, unita="mm"),
        ),
        risultato=output.geometria.d_mm, unita="mm", clausola=D_EFFICACE_CLAUSE,
        nota="Altezza utile media della sezione.",
    )


def _passo_u0(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    valori = (*valori_colonna(inputs), *valori_pi_se_circolare(inputs.lato_a_mm))
    return Passo(
        simbolo="u_0", formula=formula_perimetro(inputs.lato_a_mm), valori=valori,
        risultato=output.geometria.u0_mm, unita="mm", clausola="EN 1992-1-1 §6.4.2",
        nota="Perimetro di verifica al filo del pilastro (distanza nulla dal filo).",
    )


def _passo_ved_red_0(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float) -> Passo:
    formula = f"{KN_TO_N:g} * V_Ed * β - p * {formula_area_colonna(inputs.lato_a_mm)}"
    valori = (
        Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN", descrizione="taglio di progetto (SLU+SLV) al pilastro"),
        Valore(simbolo="β", valore=beta, descrizione="fattore di eccentricità"),
        Valore(simbolo="p", valore=inputs.pterreno_MPa, unita="MPa", descrizione="pressione del terreno da FEM"),
        *valori_colonna(inputs),
        *valori_pi_se_circolare(inputs.lato_a_mm),
    )
    return Passo(
        simbolo="V_Ed,red,0", formula=formula, valori=valori,
        risultato=output.faccia_pilastro.ved_red_0_kN, unita="kN", scala=SCALA_N_A_KN, clausola=RIDUZIONE_TERRENO_CLAUSE,
        nota="Taglio ridotto della quota di carico scaricata direttamente sul terreno entro l'impronta del pilastro; "
             "β è applicato al taglio lordo anziché al taglio già ridotto (approssimazione conservativa "
             "rispetto a β·(V_Ed − p·A) di EN1992-1-1 eq. 6.48).",
    )


def _passo_ved_0(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="v_Ed,0", formula=f"{KN_TO_N:g} * V_Ed,red,0 / (u_0 * d)",
        valori=(
            Valore(simbolo="V_Ed,red,0", valore=output.faccia_pilastro.ved_red_0_kN, unita="kN"),
            Valore(simbolo="u_0", valore=output.geometria.u0_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.faccia_pilastro.v_ed_0_MPa, unita="MPa", clausola="EN 1992-1-1 §6.4.3(1)",
        nota="Tensione di punzonamento al perimetro di verifica del filo del pilastro.",
    )


def _passo_vrd_max(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    formula = f"k_max * ({NU_COEFFICIENT:g} * (1 - f_ck / {FCK_LIMIT_FOR_NU:g})) * ({ALPHA_CC:g} * f_ck / γ_c)"
    return Passo(
        simbolo="v_Rd,max", formula=formula,
        valori=(
            Valore(simbolo="k_max", valore=inputs.coeff_vrd_max, descrizione=K_MAX_DESCRIZIONE),
            Valore(simbolo="f_ck", valore=inputs.fck_MPa, unita="MPa"),
            Valore(simbolo="γ_c", valore=GAMMA_C, descrizione="coefficiente parziale del calcestruzzo"),
        ),
        risultato=output.faccia_pilastro.v_rd_max_MPa, unita="MPa", clausola=FACCIA_CLAUSE,
        nota="Tensione massima di punzonamento al perimetro u0 (ν = 0,6·(1 − f_ck/250), f_cd = α_cc·f_ck/γ_c); "
             "nessuna armatura può innalzare questo limite.",
    )


def _passo_check_filo_pilastro(output: PunzonamentoOutput) -> Passo:
    v_ed_0, v_rd_max = output.faccia_pilastro.v_ed_0_MPa, output.faccia_pilastro.v_rd_max_MPa
    return Passo(
        simbolo="v_Ed,0", formula="v_Ed,0 < v_Rd,max",
        valori=(
            Valore(simbolo="v_Ed,0", valore=v_ed_0, unita="MPa"),
            Valore(simbolo="v_Rd,max", valore=v_rd_max, unita="MPa"),
        ),
        risultato=v_ed_0, unita="MPa", clausola=FACCIA_CLAUSE,
        esito="soddisfatta" if v_ed_0 < v_rd_max else "non soddisfatta",
        nota="Verifica a punzonamento al filo del pilastro.",
    )

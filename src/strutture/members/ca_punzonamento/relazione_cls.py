"""Traccia "Percentuale di armatura tesa e fattore dimensionale" and "Perimetro di verifica
critico": the punching-shear verification without reinforcement (EN 1992-1-1 §6.4.4), tracing only
the GOVERNING perimeter found by the scan (docs/architecture-phase2.md §5), second and third
sections of `relazione.py` (§6). `v_c` (the concrete-only term without the 2d/a enhancement) is also
returned so `relazione_armatura.py` can reuse it for u0,out without recomputing it under a different
name."""
from strutture.shared.ec2_shear import v_min as ec2_v_min
from strutture.shared.ec2_shear import v_rd_c as ec2_v_rd_c
from strutture.shared.ec2_shear.v_min import V_MIN_COEFFICIENT_EN
from strutture.shared.ec2_shear.v_rd_c import C_RD_C_COEFFICIENT_EN
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import PerimetroCriticoOutput, PunzonamentoInput, PunzonamentoOutput
from .reinforcement_ratio import RHO_MAX_WARNING
from .relazione_comune import (
    GAMMA_C,
    KN_TO_N,
    PI_GRECO,
    RIDUZIONE_TERRENO_CLAUSE,
    SCALA_N_A_KN,
    formula_area,
    formula_perimetro,
    valori_colonna,
)

RHO_CLAUSE = "EN 1992-1-1 §6.4.4(1)"
PERIMETRO_CLAUSE = "EN 1992-1-1 §6.4.4"
A_GOVERNANTE_CLAUSE = "EN 1992-1-1 §6.4.4(2)"


def traccia_rho_k(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Traccia:
    d_mm = output.geometria.d_mm
    passi = (
        _passo_rho_x(inputs, d_mm),
        _passo_rho_y(inputs, d_mm),
        _passo_rho_l(inputs, output, d_mm),
        _passo_check_rho(output),
        _passo_k(output),
    )
    return Traccia(titolo="Percentuale di armatura tesa e fattore dimensionale", passi=passi)


def traccia_perimetro_critico(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float) -> tuple[Traccia, float]:
    """Returns (traccia, v_c) — `v_c` is reused by `relazione_armatura.py`."""
    d_mm = output.geometria.d_mm
    pc = output.perimetro_critico
    v_c = ec2_v_rd_c(pc.k, pc.rho, inputs.fck_MPa, 0.0, GAMMA_C).concrete_term_MPa
    v_min = ec2_v_min(pc.k, inputs.fck_MPa)
    simbolo_area = "A_a" if inputs.a_amanuale_mm2 is None else "A_a,eff"

    passi = [_passo_a_governante(pc, d_mm), _passo_ui(inputs, pc), _passo_area(inputs, pc)]
    if inputs.a_amanuale_mm2 is not None:
        passi.append(_passo_area_effettiva(inputs, pc))
    passi += [
        _passo_ved_red_ui(inputs, pc, beta, simbolo_area),
        _passo_vc(inputs, pc, v_c),
        _passo_vmin(inputs, pc, v_min),
        _passo_vrd_i(d_mm, pc, v_c, v_min),
        _passo_ved_i(d_mm, pc),
        _passo_check_perimetro(pc),
    ]
    titolo = f"Perimetro di verifica critico — perimetro governante a/d = {pc.a_governante_su_d:.2f}".replace(".", ",")
    return Traccia(titolo=titolo, passi=tuple(passi)), v_c


def _direzione_rho(phi_mm: float, passo_mm: float, phi_add_mm: float, passo_add_mm: float, d_mm: float) -> float:
    """Mirrors `reinforcement_ratio._direction_ratio` (bar_area(φ) = π/4·φ²), restated as a formula."""
    principale = PI_GRECO * phi_mm**2 / (4.0 * passo_mm * d_mm)
    if passo_add_mm == 0:
        return principale
    return principale + PI_GRECO * phi_add_mm**2 / (4.0 * passo_add_mm * d_mm)


def _passo_rho_direzione(simbolo: str, phi: str, passo: str, phi_add: str, passo_add: str,
                          inputs_phi: float, inputs_passo: float, inputs_phi_add: float, inputs_passo_add: float,
                          d_mm: float, nota: str) -> Passo:
    formula = f"π * {phi}^2 / (4 * {passo} * d)"
    valori = [
        Valore(simbolo="π", valore=PI_GRECO),
        Valore(simbolo=phi, valore=inputs_phi, unita="mm"),
        Valore(simbolo=passo, valore=inputs_passo, unita="mm"),
        Valore(simbolo="d", valore=d_mm, unita="mm"),
    ]
    if inputs_passo_add > 0:
        formula += f" + π * {phi_add}^2 / (4 * {passo_add} * d)"
        valori += [
            Valore(simbolo=phi_add, valore=inputs_phi_add, unita="mm", descrizione="diametro delle armature aggiuntive"),
            Valore(simbolo=passo_add, valore=inputs_passo_add, unita="mm", descrizione="passo delle armature aggiuntive"),
        ]
    risultato = _direzione_rho(inputs_phi, inputs_passo, inputs_phi_add, inputs_passo_add, d_mm)
    return Passo(simbolo=simbolo, formula=formula, valori=tuple(valori), risultato=risultato, unita="-",
                 clausola=RHO_CLAUSE, nota=nota)


def _passo_rho_x(inputs: PunzonamentoInput, d_mm: float) -> Passo:
    return _passo_rho_direzione(
        "ρ_x", "φ_x", "p_x", "φ_ax", "p_ax", inputs.phix_mm, inputs.px_mm, inputs.phiaddx_mm, inputs.paddx_mm, d_mm,
        "Rapporto geometrico di armatura tesa in direzione x.",
    )


def _passo_rho_y(inputs: PunzonamentoInput, d_mm: float) -> Passo:
    return _passo_rho_direzione(
        "ρ_y", "φ_y", "p_y", "φ_ay", "p_ay", inputs.phiy_mm, inputs.py_mm, inputs.phiaddy_mm, inputs.paddy_mm, d_mm,
        "Rapporto geometrico di armatura tesa in direzione y.",
    )


def _passo_rho_l(inputs: PunzonamentoInput, output: PunzonamentoOutput, d_mm: float) -> Passo:
    rho_x = _direzione_rho(inputs.phix_mm, inputs.px_mm, inputs.phiaddx_mm, inputs.paddx_mm, d_mm)
    rho_y = _direzione_rho(inputs.phiy_mm, inputs.py_mm, inputs.phiaddy_mm, inputs.paddy_mm, d_mm)
    return Passo(
        simbolo="ρ_l", formula="sqrt(ρ_x * ρ_y)",
        valori=(Valore(simbolo="ρ_x", valore=rho_x, unita="-"), Valore(simbolo="ρ_y", valore=rho_y, unita="-")),
        risultato=output.perimetro_critico.rho, unita="-", clausola=RHO_CLAUSE,
        nota="Percentuale geometrica di armatura tesa (media geometrica delle due direzioni).",
    )


def _passo_check_rho(output: PunzonamentoOutput) -> Passo:
    rho = output.perimetro_critico.rho
    return Passo(
        simbolo="ρ_l", formula=f"ρ_l <= {RHO_MAX_WARNING:g}",
        valori=(Valore(simbolo="ρ_l", valore=rho, unita="-"),),
        risultato=rho, unita="-", clausola=RHO_CLAUSE,
        esito="soddisfatta" if rho <= RHO_MAX_WARNING else "non soddisfatta",
        nota="Oltre il limite, v_Rd,c usa comunque ρ_l limitato al 2%.",
    )


def _passo_k(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="k", formula="min(1 + sqrt(200 / d), 2)",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=output.perimetro_critico.k, unita="-", clausola="EN 1992-1-1 §6.2.2(1)",
        nota="Fattore di scala per l'effetto dimensionale, limitato a 2.",
    )


def _valore_a_gov(pc: PerimetroCriticoOutput) -> Valore:
    return Valore(simbolo="a_gov", valore=pc.a_governante_mm, unita="mm",
                   descrizione="distanza del perimetro critico governante dal filo del pilastro (a nell'output)")


def _passo_a_governante(pc: PerimetroCriticoOutput, d_mm: float) -> Passo:
    """Defines the result under `a_gov` — NEVER `a`, which `valori_colonna` already uses for the
    column side (review finding, WRONG_FORMULA): the two identifiers must stay distinct or a reader
    re-evaluating `u_i`/`A_a` (both use `a_gov` for this same distance) with the printed `a` gets the
    column side instead."""
    return Passo(
        simbolo="a_gov", formula="x_gov * d",
        valori=(
            Valore(simbolo="x_gov", valore=pc.a_governante_su_d, unita="-",
                   descrizione="rapporto a/d del perimetro governante, dalla scansione EN1992-1-1 §6.4.2 per "
                                "a/d in [0,5; 2,0] passo 0,01 che massimizza v_Ed,i/v_Rd,i ((a/d)* nell'output)"),
            Valore(simbolo="d", valore=d_mm, unita="mm"),
        ),
        risultato=pc.a_governante_mm, unita="mm", clausola=A_GOVERNANTE_CLAUSE,
        nota="Distanza del perimetro di verifica critico governante dal filo del pilastro (a nell'output, "
             "qui a_gov per non collidere col lato a del pilastro).",
    )


def _passo_ui(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput) -> Passo:
    base = formula_perimetro(inputs.lato_a_mm, distanza="a_gov")
    valori = [*valori_colonna(inputs), _valore_a_gov(pc), Valore(simbolo="π", valore=PI_GRECO)]
    if inputs.umanuale_mm is None:
        formula = base
    else:
        formula = f"min({base}, u_man)"
        valori.append(Valore(simbolo="u_man", valore=inputs.umanuale_mm, unita="mm",
                              descrizione="perimetro di verifica impostato manualmente"))
    return Passo(
        simbolo="u_i", formula=formula, valori=tuple(valori),
        risultato=pc.ui_mm, unita="mm", clausola="EN 1992-1-1 §6.4.2",
        nota="Perimetro di verifica al perimetro critico governante.",
    )


def _passo_area(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput) -> Passo:
    formula = formula_area(inputs.lato_a_mm, distanza="a_gov")
    valori = (*valori_colonna(inputs), _valore_a_gov(pc), Valore(simbolo="π", valore=PI_GRECO))
    return Passo(
        simbolo="A_a", formula=formula, valori=valori,
        risultato=pc.area_mm2, unita="mm2", clausola="EN 1992-1-1 §6.4.2",
        nota="Area racchiusa dal perimetro di verifica governante.",
    )


def _passo_area_effettiva(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput) -> Passo:
    area_eff = min(pc.area_mm2, inputs.a_amanuale_mm2)
    return Passo(
        simbolo="A_a,eff", formula="min(A_a, A_a,man)",
        valori=(
            Valore(simbolo="A_a", valore=pc.area_mm2, unita="mm2"),
            Valore(simbolo="A_a,man", valore=inputs.a_amanuale_mm2, unita="mm2",
                   descrizione="area entro il perimetro di verifica impostata manualmente"),
        ),
        risultato=area_eff, unita="mm2", clausola=PERIMETRO_CLAUSE,
        nota="Area limitata dall'impostazione manuale, in alternativa all'area geometrica del perimetro.",
    )


def _passo_ved_red_ui(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput, beta: float, simbolo_area: str) -> Passo:
    valore_area = pc.area_mm2 if inputs.a_amanuale_mm2 is None else min(pc.area_mm2, inputs.a_amanuale_mm2)
    formula = f"{KN_TO_N:g} * V_Ed * β - p * {simbolo_area}"
    return Passo(
        simbolo="V_Ed,red,ui", formula=formula,
        valori=(
            Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN"),
            Valore(simbolo="β", valore=beta),
            Valore(simbolo="p", valore=inputs.pterreno_MPa, unita="MPa"),
            Valore(simbolo=simbolo_area, valore=valore_area, unita="mm2"),
        ),
        risultato=pc.ved_red_ui_kN, unita="kN", scala=SCALA_N_A_KN, clausola=RIDUZIONE_TERRENO_CLAUSE,
        nota="Taglio ridotto della quota di carico scaricata sul terreno entro l'area del perimetro governante; "
             "β è applicato al taglio lordo anziché al taglio già ridotto (approssimazione conservativa "
             "rispetto a β·(V_Ed − p·A) di EN1992-1-1 eq. 6.48).",
    )


def _passo_vc(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput, v_c: float) -> Passo:
    formula = f"{C_RD_C_COEFFICIENT_EN:g} * k * (100 * min(ρ_l, {RHO_MAX_WARNING:g}) * f_ck)^(1/3) / γ_c"
    return Passo(
        simbolo="v_c", formula=formula,
        valori=(
            Valore(simbolo="k", valore=pc.k, unita="-"),
            Valore(simbolo="ρ_l", valore=pc.rho, unita="-"),
            Valore(simbolo="f_ck", valore=inputs.fck_MPa, unita="MPa"),
            Valore(simbolo="γ_c", valore=GAMMA_C, descrizione="coefficiente parziale del calcestruzzo"),
        ),
        risultato=v_c, unita="MPa", clausola="EN 1992-1-1 §6.4.4(1)",
        nota="Termine di base della resistenza a punzonamento del solo calcestruzzo (ρ_l limitato al 2%).",
    )


def _passo_vmin(inputs: PunzonamentoInput, pc: PerimetroCriticoOutput, v_min: float) -> Passo:
    return Passo(
        simbolo="v_min", formula=f"{V_MIN_COEFFICIENT_EN:g} * k^1.5 * sqrt(f_ck)",
        valori=(Valore(simbolo="k", valore=pc.k, unita="-"), Valore(simbolo="f_ck", valore=inputs.fck_MPa, unita="MPa")),
        risultato=v_min, unita="MPa", clausola="EN 1992-1-1 §6.2.2(1)",
        nota="Resistenza minima a taglio/punzonamento del calcestruzzo.",
    )


def _passo_vrd_i(d_mm: float, pc: PerimetroCriticoOutput, v_c: float, v_min: float) -> Passo:
    return Passo(
        simbolo="v_Rd,i", formula="max(v_c, v_min) * (2 * d / a_gov)",
        valori=(
            Valore(simbolo="v_c", valore=v_c, unita="MPa"),
            Valore(simbolo="v_min", valore=v_min, unita="MPa"),
            Valore(simbolo="d", valore=d_mm, unita="mm"),
            _valore_a_gov(pc),
        ),
        risultato=pc.v_rd_i_MPa, unita="MPa", clausola="EN 1992-1-1 §6.4.4(2)",
        nota="Resistenza a punzonamento del solo calcestruzzo al perimetro governante, con incremento 2d/a "
             "(il contributo k1·σcp non compare: nessuno sforzo normale nella piastra in questo calcolo).",
    )


def _passo_ved_i(d_mm: float, pc: PerimetroCriticoOutput) -> Passo:
    return Passo(
        simbolo="v_Ed,i", formula=f"{KN_TO_N:g} * V_Ed,red,ui / (u_i * d)",
        valori=(
            Valore(simbolo="V_Ed,red,ui", valore=pc.ved_red_ui_kN, unita="kN"),
            Valore(simbolo="u_i", valore=pc.ui_mm, unita="mm"),
            Valore(simbolo="d", valore=d_mm, unita="mm"),
        ),
        risultato=pc.v_ed_i_MPa, unita="MPa", clausola="EN 1992-1-1 §6.4.3(1)",
        nota="Tensione di punzonamento al perimetro critico governante.",
    )


def _passo_check_perimetro(pc: PerimetroCriticoOutput) -> Passo:
    return Passo(
        simbolo="v_Ed,i/v_Rd,i", formula="v_Ed,i / v_Rd,i < 1",
        valori=(
            Valore(simbolo="v_Ed,i", valore=pc.v_ed_i_MPa, unita="MPa"),
            Valore(simbolo="v_Rd,i", valore=pc.v_rd_i_MPa, unita="MPa"),
        ),
        risultato=pc.rapporto, unita="-", clausola=PERIMETRO_CLAUSE,
        esito="soddisfatta" if not pc.armatura_necessaria else "non soddisfatta",
        nota="Verifica a punzonamento al perimetro critico; se non soddisfatta serve l'armatura verticale.",
    )

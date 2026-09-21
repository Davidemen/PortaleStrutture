"""Trace of the punching-reinforcement design (EN 1992-1-1 §6.4.5/§9.4.3): "Layout radiale delle
cuciture verticali" and "Dimensionamento delle cuciture e resistenza complessiva", present only when
`PunzonamentoOutput.armatura` is not None — the fourth/fifth sections of `relazione.py`
(docs/architecture-phase2.md §6)."""
from strutture.shared.ec2_shear.fywd_ef import FYWD_EF_BASE_MPA, FYWD_EF_SLOPE
from strutture.shared.materials.rebar import GAMMA_S, rebar_properties
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import PunzonamentoInput, PunzonamentoOutput
from .relazione_comune import KN_TO_N, PI_GRECO, SCALA_N_A_KN
from .shear_reinf_design import ASW_MIN_ALPHA_FACTOR, VRD_C_ENHANCEMENT_FRACTION, VRD_CS1_ALPHA_FACTOR
from .shear_reinf_layout import A1_MAX_FACTOR, A1_MIN_FACTOR, BU_ST_MAX_FACTOR, SR_MAX_FACTOR
from .tables import STAFFA_GRADE

DETTAGLI_CLAUSE = "EN 1992-1-1 §9.4.3(1)"
ASW_MIN_CLAUSE = "EN 1992-1-1 §9.4.3(2) eq. (9.11)"
RESISTENZA_CLAUSE = "EN 1992-1-1 §6.4.5(1)/eq.(9.11)"


def traccia_armatura(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float, v_c: float) -> tuple[Traccia, ...]:
    """Empty when no reinforcement is needed (§6: "punching reinforcement if present")."""
    if output.armatura is None:
        return ()
    return (_traccia_layout(inputs, output, beta, v_c), _traccia_dimensionamento(inputs, output, beta))


def _traccia_layout(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float, v_c: float) -> Traccia:
    passi = (
        _passo_u0_out(inputs, output, beta, v_c),
        _passo_kd_primo(inputs, output),
        _passo_sr_max(output),
        _passo_a1_min(output),
        _passo_a1_max(output),
        _passo_bu_st_limite(output),
        _passo_check_a1_min(inputs, output),
        _passo_check_a1_max(inputs, output),
        _passo_check_bu(inputs, output),
        _passo_check_st(inputs, output),
        _passo_au(inputs, output),
        _passo_au_meno_a1(inputs, output),
        _passo_sr(inputs, output),
    )
    return Traccia(titolo="Layout radiale delle cuciture verticali", passi=passi)


def _traccia_dimensionamento(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float) -> Traccia:
    passi = (
        _passo_asw1(inputs, output),
        _passo_fywd_ef(output),
        _passo_asw_min(inputs, output),
        _passo_check_asw_min(output),
        _passo_vrd_cs_min(output),
        _passo_vrd_cs1(output),
        _passo_vrd_c_primo(output),
        _passo_vrd_s(inputs, output),
        _passo_vrrd(output),
        _passo_check_finale(inputs, output, beta),
    )
    return Traccia(titolo="Dimensionamento delle cuciture e resistenza complessiva", passi=passi)


def _passo_u0_out(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float, v_c: float) -> Passo:
    return Passo(
        simbolo="u_0,out", formula=f"{KN_TO_N:g} * V_Ed * β / (v_c * d)",
        valori=(
            Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN"),
            Valore(simbolo="β", valore=beta),
            Valore(simbolo="v_c", valore=v_c, unita="MPa",
                   descrizione="termine di base della resistenza del calcestruzzo, senza incremento 2d/a"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.armatura.u0_out_mm, unita="mm", clausola="EN 1992-1-1 §6.4.5(4)",
        nota="Perimetro oltre il quale il solo calcestruzzo basta, senza armatura a taglio.",
    )


def _passo_kd_primo(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="k'd", formula="(u_0,out - 2 * (a + b)) / (2 * π)",
        valori=(
            Valore(simbolo="u_0,out", valore=output.armatura.u0_out_mm, unita="mm"),
            Valore(simbolo="a", valore=inputs.lato_a_mm, unita="mm", descrizione="lato 1 del pilastro (0 per pilastro circolare)"),
            Valore(simbolo="b", valore=inputs.lato_b_mm, unita="mm", descrizione="lato 2 del pilastro (0 per pilastro circolare)"),
            Valore(simbolo="π", valore=PI_GRECO),
        ),
        risultato=output.armatura.k_d_primo_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Raggio oltre i lati rettilinei del pilastro necessario a raggiungere u0,out.",
    )


def _passo_sr_max(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="s_r,max", formula=f"{SR_MAX_FACTOR:g} * d",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=output.armatura.sr_max_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Passo massimo radiale ammesso tra le file di cuciture.",
    )


def _passo_a1_min(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="a_1,min", formula=f"{A1_MIN_FACTOR:g} * d",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=output.armatura.a1_min_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Distanza minima della prima fila di cuciture dal filo del pilastro.",
    )


def _passo_a1_max(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="a_1,max", formula=f"{A1_MAX_FACTOR:g} * d",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=output.armatura.a1_max_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Distanza massima della prima fila di cuciture dal filo del pilastro.",
    )


def _passo_bu_st_limite(output: PunzonamentoOutput) -> Passo:
    limite = BU_ST_MAX_FACTOR * output.geometria.d_mm
    return Passo(
        simbolo="b_u,lim", formula=f"{BU_ST_MAX_FACTOR:g} * d",
        valori=(Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),),
        risultato=limite, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Limite condiviso dalla distanza dell'ultima fila e dal passo tangenziale delle cuciture.",
    )


def _passo_check_a1_min(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    a1eff, a1min = inputs.a1eff_mm, output.armatura.a1_min_mm
    return Passo(
        simbolo="a_1,eff", formula="a_1,eff >= a_1,min",
        valori=(Valore(simbolo="a_1,eff", valore=a1eff, unita="mm"), Valore(simbolo="a_1,min", valore=a1min, unita="mm")),
        risultato=a1eff, unita="mm", clausola=DETTAGLI_CLAUSE,
        esito="soddisfatta" if a1eff >= a1min else "non soddisfatta",
        nota="Distanza minima della prima fila di cuciture dal filo del pilastro.",
    )


def _passo_check_a1_max(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    a1eff, a1max = inputs.a1eff_mm, output.armatura.a1_max_mm
    return Passo(
        simbolo="a_1,eff", formula="a_1,eff <= a_1,max",
        valori=(Valore(simbolo="a_1,eff", valore=a1eff, unita="mm"), Valore(simbolo="a_1,max", valore=a1max, unita="mm")),
        risultato=a1eff, unita="mm", clausola=DETTAGLI_CLAUSE,
        esito="soddisfatta" if a1eff <= a1max else "non soddisfatta",
        nota="Distanza massima della prima fila di cuciture dal filo del pilastro.",
    )


def _passo_check_bu(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    limite = BU_ST_MAX_FACTOR * output.geometria.d_mm
    return Passo(
        simbolo="b_u", formula="b_u < b_u,lim",
        valori=(Valore(simbolo="b_u", valore=inputs.bu_mm, unita="mm"), Valore(simbolo="b_u,lim", valore=limite, unita="mm")),
        risultato=inputs.bu_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        esito="soddisfatta" if inputs.bu_mm < limite else "non soddisfatta",
        nota="Distanza massima dell'ultima fila di cuciture dal perimetro u0,out.",
    )


def _passo_check_st(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    limite = BU_ST_MAX_FACTOR * output.geometria.d_mm
    return Passo(
        simbolo="s_t", formula="s_t < b_u,lim",
        valori=(Valore(simbolo="s_t", valore=inputs.st_mm, unita="mm"), Valore(simbolo="b_u,lim", valore=limite, unita="mm")),
        risultato=inputs.st_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        esito="soddisfatta" if inputs.st_mm < limite else "non soddisfatta",
        nota="Passo tangenziale massimo tra le cuciture di una stessa fila.",
    )


def _passo_au(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="a_u", formula="k'd - b_u",
        valori=(
            Valore(simbolo="k'd", valore=output.armatura.k_d_primo_mm, unita="mm"),
            Valore(simbolo="b_u", valore=inputs.bu_mm, unita="mm"),
        ),
        risultato=output.armatura.au_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Distanza dell'ultima fila di cuciture dal filo del pilastro.",
    )


def _passo_au_meno_a1(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="a_u-a_1", formula="a_u - a_1,eff",
        valori=(
            Valore(simbolo="a_u", valore=output.armatura.au_mm, unita="mm"),
            Valore(simbolo="a_1,eff", valore=inputs.a1eff_mm, unita="mm"),
        ),
        risultato=output.armatura.au_meno_a1_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Distanza tra la prima e l'ultima fila di cuciture.",
    )


def _passo_sr(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="s_r", formula="(a_u - a_1,eff) / (n_file - 1)",
        valori=(
            Valore(simbolo="a_u", valore=output.armatura.au_mm, unita="mm"),
            Valore(simbolo="a_1,eff", valore=inputs.a1eff_mm, unita="mm"),
            Valore(simbolo="n_file", valore=float(output.armatura.n_file),
                   descrizione="numero di file radiali di cuciture, arrotondato per eccesso da (a_u-a_1)/s_r,max + 1"),
        ),
        risultato=output.armatura.sr_mm, unita="mm", clausola=DETTAGLI_CLAUSE,
        nota="Interasse radiale effettivo tra le file di cuciture.",
    )


def _passo_asw1(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="A_sw,1", formula="π * φ_w^2 / 4",
        valori=(
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ_w", valore=inputs.phi_staffa_mm, unita="mm", descrizione="diametro delle cuciture verticali"),
        ),
        risultato=output.armatura.area_staffa_mm2, unita="mm2",
        nota="Area di una cucitura verticale.",
    )


def _passo_fywd_ef(output: PunzonamentoOutput) -> Passo:
    fyk_w = rebar_properties(STAFFA_GRADE).fyk_MPa
    return Passo(
        simbolo="f_ywd,ef", formula=f"min({FYWD_EF_BASE_MPA:g} + {FYWD_EF_SLOPE:g} * d, f_yk,w / γ_s)",
        valori=(
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
            Valore(simbolo="f_yk,w", valore=fyk_w, unita="MPa",
                   descrizione=f"tensione caratteristica di snervamento delle cuciture ({STAFFA_GRADE}, fissa)"),
            Valore(simbolo="γ_s", valore=GAMMA_S, descrizione="coefficiente parziale dell'acciaio"),
        ),
        risultato=output.armatura.fywd_ef_MPa, unita="MPa", clausola="EN 1992-1-1 §6.4.5(1) eq. (6.52)",
        nota="Tensione di calcolo efficace delle cuciture, limitata alla tensione di calcolo fywd.",
    )


def _passo_asw_min(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    fyk_w = rebar_properties(STAFFA_GRADE).fyk_MPa
    formula = f"0.08 * sqrt(f_ck) * s_r * s_t / (f_yk,w * {ASW_MIN_ALPHA_FACTOR:g})"
    return Passo(
        simbolo="A_sw,min", formula=formula,
        valori=(
            Valore(simbolo="f_ck", valore=inputs.fck_MPa, unita="MPa"),
            Valore(simbolo="s_r", valore=output.armatura.sr_mm, unita="mm"),
            Valore(simbolo="s_t", valore=inputs.st_mm, unita="mm", descrizione="passo tangenziale delle cuciture di una stessa fila"),
            Valore(simbolo="f_yk,w", valore=fyk_w, unita="MPa"),
        ),
        risultato=output.armatura.asw_min_mm2, unita="mm2", clausola=ASW_MIN_CLAUSE,
        nota="Area minima di ogni cucitura verticale.",
    )


def _passo_check_asw_min(output: PunzonamentoOutput) -> Passo:
    area, minimo = output.armatura.area_staffa_mm2, output.armatura.asw_min_mm2
    return Passo(
        simbolo="A_sw,1", formula="A_sw,1 >= A_sw,min",
        valori=(Valore(simbolo="A_sw,1", valore=area, unita="mm2"), Valore(simbolo="A_sw,min", valore=minimo, unita="mm2")),
        risultato=area, unita="mm2", clausola=ASW_MIN_CLAUSE,
        esito="soddisfatta" if area >= minimo else "non soddisfatta",
        nota="La cucitura scelta deve avere area non inferiore al minimo.",
    )


def _passo_vrd_cs_min(output: PunzonamentoOutput) -> Passo:
    pc = output.perimetro_critico
    formula = f"(v_Ed,i - {VRD_C_ENHANCEMENT_FRACTION:g} * v_Rd,i) * u_i * d"
    return Passo(
        simbolo="V'_Rd,cs,min", formula=formula,
        valori=(
            Valore(simbolo="v_Ed,i", valore=pc.v_ed_i_MPa, unita="MPa"),
            Valore(simbolo="v_Rd,i", valore=pc.v_rd_i_MPa, unita="MPa"),
            Valore(simbolo="u_i", valore=pc.ui_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.armatura.v_rd_cs_min_kN, unita="kN", scala=SCALA_N_A_KN, clausola=RESISTENZA_CLAUSE,
        nota="Forza lato acciaio richiesta al perimetro governante (EC2 eq. 6.52 riarrangiata).",
    )


def _passo_vrd_cs1(output: PunzonamentoOutput) -> Passo:
    formula = f"{VRD_CS1_ALPHA_FACTOR:g} * (d / s_r) * A_sw,1 * f_ywd,ef"
    return Passo(
        simbolo="V_Rd,cs(1)", formula=formula,
        valori=(
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
            Valore(simbolo="s_r", valore=output.armatura.sr_mm, unita="mm"),
            Valore(simbolo="A_sw,1", valore=output.armatura.area_staffa_mm2, unita="mm2"),
            Valore(simbolo="f_ywd,ef", valore=output.armatura.fywd_ef_MPa, unita="MPa"),
        ),
        risultato=output.armatura.v_rd_cs1_kN, unita="kN", scala=SCALA_N_A_KN, clausola=RESISTENZA_CLAUSE,
        nota="Resistenza di una cucitura sommata lungo una fila circonferenziale completa.",
    )


def _passo_vrd_c_primo(output: PunzonamentoOutput) -> Passo:
    pc = output.perimetro_critico
    return Passo(
        simbolo="V'_Rd,c", formula=f"{VRD_C_ENHANCEMENT_FRACTION:g} * v_Rd,i * u_i * d",
        valori=(
            Valore(simbolo="v_Rd,i", valore=pc.v_rd_i_MPa, unita="MPa"),
            Valore(simbolo="u_i", valore=pc.ui_mm, unita="mm"),
            Valore(simbolo="d", valore=output.geometria.d_mm, unita="mm"),
        ),
        risultato=output.armatura.v_rd_c_primo_kN, unita="kN", scala=SCALA_N_A_KN, clausola=RESISTENZA_CLAUSE,
        nota="Contributo del calcestruzzo alla resistenza complessiva con armatura.",
    )


def _passo_vrd_s(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="V_Rd,s", formula="n * V_Rd,cs1",
        valori=(
            Valore(simbolo="n", valore=float(inputs.n_staffe), descrizione="numero effettivo di cuciture per fila circonferenziale"),
            Valore(simbolo="V_Rd,cs1", valore=output.armatura.v_rd_cs1_kN, unita="kN",
                   descrizione="resistenza di una cucitura per fila (V_Rd,cs(1) nell'output)"),
        ),
        risultato=output.armatura.v_rd_s_kN, unita="kN", clausola=RESISTENZA_CLAUSE,
        nota="Contributo delle cuciture alla resistenza complessiva.",
    )


def _passo_vrrd(output: PunzonamentoOutput) -> Passo:
    return Passo(
        simbolo="V_Rrd", formula="V'_Rd,c + V_Rd,s",
        valori=(
            Valore(simbolo="V'_Rd,c", valore=output.armatura.v_rd_c_primo_kN, unita="kN"),
            Valore(simbolo="V_Rd,s", valore=output.armatura.v_rd_s_kN, unita="kN"),
        ),
        risultato=output.armatura.v_rrd_kN, unita="kN", clausola=RESISTENZA_CLAUSE,
        nota="Resistenza complessiva a punzonamento con armatura verticale.",
    )


def _passo_check_finale(inputs: PunzonamentoInput, output: PunzonamentoOutput, beta: float) -> Passo:
    v_rrd = output.armatura.v_rrd_kN
    ved_beta = inputs.ved_kN * beta
    return Passo(
        simbolo="V_Ed/V_Rd", formula="V_Ed * β / V_Rrd < 1",
        valori=(
            Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN"),
            Valore(simbolo="β", valore=beta),
            Valore(simbolo="V_Rrd", valore=v_rrd, unita="kN"),
        ),
        risultato=output.armatura.ved_su_vrd, unita="-", clausola=RESISTENZA_CLAUSE,
        esito="soddisfatta" if v_rrd > ved_beta else "non soddisfatta",
        nota="Tasso di sfruttamento finale della resistenza a punzonamento con armatura.",
    )

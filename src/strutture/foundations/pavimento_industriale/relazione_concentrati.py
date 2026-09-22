"""Verified restatement (docs/architecture-phase2.md) of `concentrati_contatto.py`/`concentrati_
tensioni.py`/`concentrati_punzonamento.py` (Westergaard point-load stresses at centro/bordo/spigolo
+ EC2 §6.4-style punching) composed via `concentrati.py`'s "many-rows result" (`righe`+`inviluppo`+
`governante`, docs/architecture-phase2.md §5: "many-rows tools trace the GOVERNING row only").

The 3 Westergaard position formulas are each demonstrated once, on the OVERALL governing case's own
row for that position (`output.concentrati.governante.caso`, usually all 3 positions of one wheel-
load case) — covering "interior/edge/corner" literally, with real numbers, not a template. Each of
the 5 Check steps then cites ITS OWN governing row (`inviluppo`, which need not be the same row for
every quantity — punching u0/u1 routinely governs from a different case/position than the bending
checks) via `inputs.carichi`/`output.concentrati.righe`, so the check is always numerically honest
even when it is not the position demonstrated above it.

Standard mode only (this module is never called with `legacy_compat=True`): `u1`'s edge/corner
control perimeter uses the effective depth `d`, not the sheet's `h` (`concentrati_punzonamento.py`'s
own docstring, review-equivalent fix already in the calculation code, restated as-is).

Every `TL_*` envelope Check names its own governing case/position IN THE `simbolo` itself (not only
in `nota`/`Valore.descrizione`, neither of which `traccia_a_testo` ever prints): each envelope row
can substitute β/P/b_x/b_y from a DIFFERENT load-table row than its neighbours (`u0`/`u1` routinely
governs from a different row than the bending checks, see `traccia_verifiche_concentrati`'s own
docstring) — printing only "(inviluppo)" left the reader unable to tell which case/position each
number came from (review finding MISLEADING)."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura import ArmaturaResult
from .carico_row import CaricoRow
from .concentrati import ConcentratiResult, EnvelopeRow
from .concentrati_riga import RigaCaricoResult
from .materiali import MaterialiResult
from .models import PavimentoIndustrialeInput
from .sottofondo import SottofondoResult
from .tables import BETA_PUNZONAMENTO, WESTERGAARD_BORDO, WESTERGAARD_CENTRO, WESTERGAARD_SPIGOLO

PI_GRECO = math.pi
CLAUSOLA_WESTERGAARD = "CNR-DT211/2014"
CLAUSOLA_PUNZ_U0 = "EC2 §6.4.5"
CLAUSOLA_PUNZ_U1 = "EC2 §6.4.4"
_COEFFICIENTI_POSIZIONE = {"centro": WESTERGAARD_CENTRO, "bordo": WESTERGAARD_BORDO, "spigolo": WESTERGAARD_SPIGOLO}


def _riga_input(inputs: PavimentoIndustrialeInput, caso: str, posizione: str) -> CaricoRow:
    return next(r for r in inputs.carichi if r.caso == caso and r.posizione == posizione)


def _riga_output(concentrati: ConcentratiResult, caso: str, posizione: str) -> RigaCaricoResult:
    return next(r for r in concentrati.righe if r.caso == caso and r.posizione == posizione)


def _governante(concentrati: ConcentratiResult, grandezza: str) -> EnvelopeRow:
    return next(e for e in concentrati.inviluppo if e.grandezza == grandezza)


def _rr_mm(riga: CaricoRow) -> float:
    return math.sqrt(riga.impronta_a_mm * riga.impronta_b_mm / math.pi)


def _v_rd_max_mpa(inputs: PavimentoIndustrialeInput, mat: MaterialiResult) -> float:
    """`VRd,max = c·0,6·(1−fck/250)·(0,85·fck/γc)` (`concentrati_punzonamento.py`'s own formula,
    position/row-independent — computed once, reused by every row-specific punching check)."""
    v1 = 0.6 * (1.0 - mat.fck_MPa / 250.0)
    fcd_mpa = 0.85 * mat.fck_MPa / inputs.gamma_c
    return inputs.coeff_vrd_max * v1 * fcd_mpa


def _formula_u1(posizione: str) -> str:
    """`concentrati_punzonamento._u1_mm`, standard mode (`d` for every position, not the sheet's
    `h` for bordo/spigolo, `concentrati_punzonamento.py`'s own review-equivalent fix). `centro`
    reuses `shared.ec2_shear.control_perimeter`'s standard rounded-rectangle perimeter at distance
    `2d`: `u = 2(bx+by) + 2π·(2d) = 2(bx+by) + 4πd`; `bordo`/`spigolo` keep the sheet's own
    reduced-perimeter shape (not a column surrounded on all sides)."""
    if posizione == "centro":
        return "2 * (b_x + b_y) + 4 * π * d"
    if posizione == "bordo":
        return "2 * min(b_x, b_y) + max(b_x, b_y) + 2 * d * π"
    return "min(b_x, b_y) + max(b_x, b_y) + d * π"


# ---------------------------------------------------------------------------------------------
# Traccia 1: geometria di contatto (riga governante) + resistenze di punzonamento (globali)
# ---------------------------------------------------------------------------------------------


def traccia_geometria_e_resistenze(
    inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, concentrati: ConcentratiResult,
) -> Traccia:
    """3 passi (nessun Check): b (raggio di contatto corretto, riga con il tasso di lavoro
    complessivo massimo), V_Rd,max e V_Rd,c (globali, punzonamento, riusati da ogni riga)."""
    riga = _riga_input(inputs, concentrati.governante.caso, concentrati.governante.posizione)
    return Traccia(
        titolo="Carichi concentrati: geometria di contatto e resistenze di punzonamento",
        passi=(_passo_b(inputs, riga), _passo_vrd_max(inputs, mat), _passo_vrd_c(mat, sott)),
    )


def _passo_b(inputs: PavimentoIndustrialeInput, riga: CaricoRow) -> Passo:
    rr_mm = _rr_mm(riga)
    corretto = rr_mm / inputs.h_mm < 1.724
    if corretto:
        formula = "sqrt(1.6 * (b_x * b_y / π) + h^2) - 0.675 * h"
        valori = (
            Valore(simbolo="b_x", valore=riga.impronta_a_mm, unita="mm", descrizione=f"impronta di carico, dimensione x (riga governante {riga.caso}/{riga.posizione})"),
            Valore(simbolo="b_y", valore=riga.impronta_b_mm, unita="mm", descrizione="impronta di carico, dimensione y"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
        )
    else:
        formula = "sqrt(b_x * b_y / π)"
        valori = (
            Valore(simbolo="b_x", valore=riga.impronta_a_mm, unita="mm", descrizione=f"impronta di carico, dimensione x (riga governante {riga.caso}/{riga.posizione})"),
            Valore(simbolo="b_y", valore=riga.impronta_b_mm, unita="mm", descrizione="impronta di carico, dimensione y"),
            Valore(simbolo="π", valore=PI_GRECO),
        )
    return Passo(
        simbolo="b", formula=formula, valori=valori,
        risultato=_b_westergaard(rr_mm, inputs.h_mm), unita="mm", clausola=CLAUSOLA_WESTERGAARD,
        nota=f"Raggio di contatto corretto (Westergaard): r_r/h={rr_mm / inputs.h_mm:.4g} "
             f"{'<' if corretto else '≥'} 1,724, quindi "
             + ("si usa la formula corretta (non il raggio equivalente r_r direttamente)." if corretto
                else "b coincide con il raggio equivalente di contatto r_r=sqrt(Ac/π)."),
    )


def _b_westergaard(rr_mm: float, h_mm: float) -> float:
    if rr_mm / h_mm < 1.724:
        return math.sqrt(1.6 * rr_mm**2 + h_mm**2) - 0.675 * h_mm
    return rr_mm


def _passo_vrd_max(inputs: PavimentoIndustrialeInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="V_Rd,max", formula="c * 0.6 * (1 - f_ck / 250) * (0.85 * f_ck / γ_c)",
        valori=(
            Valore(simbolo="c", valore=inputs.coeff_vrd_max, descrizione="coefficiente nazionale EC2 §6.4.5(3) scelto dall'ingegnere"),
            Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),
            Valore(simbolo="γ_c", valore=inputs.gamma_c, descrizione="coefficiente parziale di sicurezza del calcestruzzo"),
        ),
        risultato=_v_rd_max_mpa(inputs, mat), unita="MPa", clausola=CLAUSOLA_PUNZ_U0,
        nota="Tensione massima di punzonamento a filo impronta, riusata da ogni riga di carico.",
    )


def _passo_vrd_c(mat: MaterialiResult, sott: SottofondoResult) -> Passo:
    return Passo(
        simbolo="V_Rd,c", formula="0.035 * min(1 + sqrt(200 / d), 2)^1.5 * sqrt(f_ck)",
        valori=(
            Valore(simbolo="d", valore=sott.d_mm, unita="mm", descrizione="altezza utile della piastra, calcolata sopra"),
            Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),
        ),
        risultato=sott.v_min_MPa, unita="MPa", clausola=CLAUSOLA_PUNZ_U1,
        nota="Resistenza a punzonamento del solo calcestruzzo (EC2 §6.2.2 vmin), riusata da ogni riga di carico.",
    )


# ---------------------------------------------------------------------------------------------
# Traccia 2: tensioni di Westergaard, posizioni interno/bordo/spigolo (caso governante)
# ---------------------------------------------------------------------------------------------


def traccia_tensioni_westergaard(inputs: PavimentoIndustrialeInput, sott: SottofondoResult, concentrati: ConcentratiResult) -> Traccia:
    """Fino a 3 passi (nessun Check): σc,max alle 3 posizioni interno/bordo/spigolo, per le righe
    del caso di carico governante."""
    caso = concentrati.governante.caso
    passi = tuple(
        _passo_sigma(inputs, sott, _riga_input(inputs, caso, riga.posizione), riga)
        for riga in concentrati.righe if riga.caso == caso
    )
    return Traccia(titolo="Carichi concentrati: tensioni di Westergaard (interno/bordo/spigolo)", passi=passi)


def _formula_sigma(posizione: str) -> str:
    if posizione in ("centro", "bordo"):
        return "k_1 * (P * 1000) / h^2 * (log10(l / b) + k_2)"
    return "k_1 * (P * 1000) / h^2 * (1 - k_3 * (r_r / l)^k_4)"


def _valori_sigma(inputs: PavimentoIndustrialeInput, sott: SottofondoResult, riga_in: CaricoRow, riga_out: RigaCaricoResult, p_kn: float) -> tuple[Valore, ...]:
    posizione = riga_in.posizione
    comuni_p_h = (
        Valore(simbolo="P", valore=p_kn, unita="kN", descrizione=f"carico, riga {riga_in.caso}/{posizione}"),
        Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
    )
    if posizione in ("centro", "bordo"):
        k1, k2 = _COEFFICIENTI_POSIZIONE[posizione]
        return (
            Valore(simbolo="k_1", valore=k1, descrizione=f"coefficiente di Westergaard, posizione {posizione}"),
            *comuni_p_h,
            Valore(simbolo="l", valore=sott.l_mm, unita="mm", descrizione="raggio di rigidezza relativa di Westergaard, calcolato sopra"),
            Valore(simbolo="b", valore=riga_out.b_mm, unita="mm", descrizione="raggio di contatto corretto (Westergaard)"),
            Valore(simbolo="k_2", valore=k2, descrizione=f"coefficiente di Westergaard, posizione {posizione}"),
        )
    k1, k3, k4 = _COEFFICIENTI_POSIZIONE[posizione]
    return (
        Valore(simbolo="k_1", valore=k1, descrizione="coefficiente di Westergaard, posizione spigolo"),
        *comuni_p_h,
        Valore(simbolo="k_3", valore=k3, descrizione="coefficiente di Westergaard, posizione spigolo"),
        Valore(simbolo="r_r", valore=_rr_mm(riga_in), unita="mm", descrizione="raggio equivalente di contatto, r_r=sqrt(Ac/π)"),
        Valore(simbolo="l", valore=sott.l_mm, unita="mm", descrizione="raggio di rigidezza relativa di Westergaard, calcolato sopra"),
        Valore(simbolo="k_4", valore=k4, descrizione="coefficiente di Westergaard, posizione spigolo"),
    )


def _passo_sigma(inputs: PavimentoIndustrialeInput, sott: SottofondoResult, riga_in: CaricoRow, riga_out: RigaCaricoResult) -> Passo:
    posizione = riga_in.posizione
    p_slu_kn = riga_in.p_kN * riga_in.gamma
    return Passo(
        simbolo=f"σ_c,max ({posizione})", formula=_formula_sigma(posizione),
        valori=_valori_sigma(inputs, sott, riga_in, riga_out, p_slu_kn),
        risultato=riga_out.sigma_c_max_MPa, unita="MPa", clausola=CLAUSOLA_WESTERGAARD,
        nota=f"Tensione di flessione ULS (Westergaard) sotto un carico concentrato, posizione {posizione} "
             f"(riga {riga_in.caso}), P=P_SLU=P·γ.",
    )


# ---------------------------------------------------------------------------------------------
# Traccia 3: verifiche dei carichi concentrati (5 Check + il tasso di lavoro massimo, highlight)
# ---------------------------------------------------------------------------------------------


def traccia_verifiche_concentrati(
    inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, arm: ArmaturaResult, concentrati: ConcentratiResult,
) -> Traccia:
    """6 passi: i 5 Check di `concentrati.py::GRANDEZZE` (uno per riga governante di quella
    grandezza) e il tasso di lavoro massimo complessivo (highlight)."""
    return Traccia(
        titolo="Verifiche dei carichi concentrati",
        passi=(
            _passo_check_tensionale(inputs, mat, concentrati),
            _passo_check_fessurazione(inputs, mat, sott, concentrati),
            _passo_check_armatura(inputs, arm, concentrati),
            _passo_check_punzonamento_u0(inputs, mat, sott, concentrati),
            _passo_check_punzonamento_u1(inputs, mat, sott, concentrati),
            _passo_tl_max(concentrati),
        ),
    )


def _riga_del_governante(inputs: PavimentoIndustrialeInput, concentrati: ConcentratiResult, grandezza: str) -> tuple[CaricoRow, RigaCaricoResult]:
    governante = _governante(concentrati, grandezza)
    return _riga_input(inputs, governante.caso, governante.posizione), _riga_output(concentrati, governante.caso, governante.posizione)


def _passo_check_tensionale(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, concentrati: ConcentratiResult) -> Passo:
    riga_in, riga_out = _riga_del_governante(inputs, concentrati, "Tensionale (Westergaard)")
    soddisfatta = riga_out.tl_tensionale <= 1.0
    return Passo(
        simbolo=f"TL_σ (inviluppo — {riga_in.caso}, posizione {riga_in.posizione})", formula="σ_c,max / f_cfd <= 1",
        valori=(
            Valore(simbolo="σ_c,max", valore=riga_out.sigma_c_max_MPa, unita="MPa", descrizione=f"riga governante {riga_in.caso}/{riga_in.posizione}, stessa formula mostrata sopra per questa posizione"),
            Valore(simbolo="f_cfd", valore=mat.fcfd_MPa, unita="MPa", descrizione="resistenza di calcolo a trazione per flessione, calcolata sopra"),
        ),
        risultato=riga_out.tl_tensionale, unita="-", clausola=CLAUSOLA_WESTERGAARD,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di lavoro tensionale, inviluppo sulle righe della tabella carichi.",
    )


def _passo_check_fessurazione(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, concentrati: ConcentratiResult) -> Passo:
    riga_in, riga_out = _riga_del_governante(inputs, concentrati, "Fessurazione")
    p_sle_freq_kn = riga_in.p_kN * riga_in.psi1
    soddisfatta = riga_out.tl_fessurazione <= 1.0
    formula = f"({_formula_sigma(riga_in.posizione)}) / (f_ctm / 1.2) <= 1"
    return Passo(
        simbolo=f"TL_f (inviluppo — {riga_in.caso}, posizione {riga_in.posizione})", formula=formula,
        valori=(
            *_valori_sigma(inputs, sott, riga_in, riga_out, p_sle_freq_kn),
            Valore(simbolo="f_ctm", valore=mat.fctm_MPa, unita="MPa", descrizione="resistenza media a trazione (CNR-DT211, da Rck), calcolata sopra"),
        ),
        risultato=riga_out.tl_fessurazione, unita="-", clausola=CLAUSOLA_WESTERGAARD,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Tasso di lavoro a fessurazione, riga governante {riga_in.caso}/{riga_in.posizione} "
             "(stessa forma della tensione ULS, con P_SLE,f=P·ψ_1 al posto di P_SLU).",
    )


def _passo_check_armatura(inputs: PavimentoIndustrialeInput, arm: ArmaturaResult, concentrati: ConcentratiResult) -> Passo:
    riga_in, riga_out = _riga_del_governante(inputs, concentrati, "Armatura")
    soddisfatta = riga_out.tl_armatura <= 1.0
    return Passo(
        simbolo=f"TL_As (inviluppo — {riga_in.caso}, posizione {riga_in.posizione})", formula="(σ_c,max * h^2 / 6) / M_Rd <= 1",
        valori=(
            Valore(simbolo="σ_c,max", valore=riga_out.sigma_c_max_MPa, unita="MPa", descrizione=f"riga governante {riga_in.caso}/{riga_in.posizione}"),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
            Valore(simbolo="M_Rd", valore=arm.mrd_Nmm_m, unita="N·m/m", descrizione="momento resistente della sezione armata, calcolato sopra (N·m/m, non Nmm/m: v. relazione_materiali_sottofondo.py)"),
        ),
        risultato=riga_out.tl_armatura, unita="-", clausola=CLAUSOLA_WESTERGAARD,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di lavoro dell'armatura: momento nominale σc,max·h²/6 su momento resistente Mrd.",
    )


def _passo_check_punzonamento_u0(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, concentrati: ConcentratiResult) -> Passo:
    riga_in, riga_out = _riga_del_governante(inputs, concentrati, "Punzonamento a u0")
    beta = BETA_PUNZONAMENTO[riga_in.posizione]
    soddisfatta = riga_out.tl_punzonamento_u0 <= 1.0
    return Passo(
        simbolo=f"TL_u0 (inviluppo — {riga_in.caso}, posizione {riga_in.posizione})", formula="(P * γ * β) * 1000 / (2 * (b_x + b_y) * d) / V_Rd,max <= 1",
        valori=(
            Valore(simbolo="P", valore=riga_in.p_kN, unita="kN", descrizione=f"carico concentrato d'ingresso, riga governante {riga_in.caso}/{riga_in.posizione}"),
            Valore(simbolo="γ", valore=riga_in.gamma, descrizione="coefficiente parziale del carico"),
            Valore(simbolo="β", valore=beta, descrizione=f"fattore di incremento del taglio per punzonamento, posizione {riga_in.posizione} (EC2 6.4.3-style)"),
            Valore(simbolo="b_x", valore=riga_in.impronta_a_mm, unita="mm", descrizione="impronta di carico, dimensione x"),
            Valore(simbolo="b_y", valore=riga_in.impronta_b_mm, unita="mm", descrizione="impronta di carico, dimensione y"),
            Valore(simbolo="d", valore=sott.d_mm, unita="mm", descrizione="altezza utile della piastra, calcolata sopra"),
            Valore(simbolo="V_Rd,max", valore=_v_rd_max_mpa(inputs, mat), unita="MPa", descrizione="tensione massima di punzonamento a filo impronta, calcolata sopra"),
        ),
        risultato=riga_out.tl_punzonamento_u0, unita="-", clausola=CLAUSOLA_PUNZ_U0,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Punzonamento al perimetro u0=2(bx+by), a filo impronta; VEd=P_SLU·β; riga governante "
             f"{riga_in.caso}/{riga_in.posizione}.",
    )


def _passo_check_punzonamento_u1(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, concentrati: ConcentratiResult) -> Passo:
    riga_in, riga_out = _riga_del_governante(inputs, concentrati, "Punzonamento a u1")
    beta = BETA_PUNZONAMENTO[riga_in.posizione]
    soddisfatta = riga_out.tl_punzonamento_u1 <= 1.0
    formula = f"(P * γ * β) * 1000 / (({_formula_u1(riga_in.posizione)}) * d) / V_Rd,c <= 1"
    return Passo(
        simbolo=f"TL_u1 (inviluppo — {riga_in.caso}, posizione {riga_in.posizione})", formula=formula,
        valori=(
            Valore(simbolo="P", valore=riga_in.p_kN, unita="kN", descrizione=f"carico concentrato d'ingresso, riga governante {riga_in.caso}/{riga_in.posizione}"),
            Valore(simbolo="γ", valore=riga_in.gamma, descrizione="coefficiente parziale del carico"),
            Valore(simbolo="β", valore=beta, descrizione=f"fattore di incremento del taglio per punzonamento, posizione {riga_in.posizione} (EC2 6.4.3-style)"),
            Valore(simbolo="b_x", valore=riga_in.impronta_a_mm, unita="mm", descrizione="impronta di carico, dimensione x"),
            Valore(simbolo="b_y", valore=riga_in.impronta_b_mm, unita="mm", descrizione="impronta di carico, dimensione y"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="d", valore=sott.d_mm, unita="mm", descrizione="altezza utile della piastra, calcolata sopra"),
            Valore(simbolo="V_Rd,c", valore=sott.v_min_MPa, unita="MPa", descrizione="resistenza a punzonamento del solo calcestruzzo, calcolata sopra"),
        ),
        risultato=riga_out.tl_punzonamento_u1, unita="-", clausola=CLAUSOLA_PUNZ_U1,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Punzonamento al perimetro u1, a distanza 2d dall'impronta; riga governante "
             f"{riga_in.caso}/{riga_in.posizione}; perimetro u1 usa l'altezza utile d per ogni "
             "posizione (correzione rispetto allo spessore h del foglio per bordo/spigolo).",
    )


def _passo_tl_max(concentrati: ConcentratiResult) -> Passo:
    governante = concentrati.governante
    return Passo(
        simbolo="TL_max", formula="TL_max",
        valori=(
            Valore(
                simbolo="TL_max", valore=governante.utilizzo_max, unita="-",
                descrizione=f"tasso di lavoro massimo fra tutte le verifiche della riga governante {governante.caso}/{governante.posizione}",
            ),
        ),
        risultato=governante.utilizzo_max, unita="-",
        nota=f"Tasso di lavoro massimo complessivo dei carichi concentrati, riga governante "
             f"{governante.caso}/{governante.posizione}.",
    )

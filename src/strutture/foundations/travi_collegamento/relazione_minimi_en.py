"""Verified restatement (docs/architecture-phase2.md) of `armatura_minima_en.py` (EN1998-1
§5.8.2(4)), `geometria_minima_en.py` (EN1998-1 minimum section geometry, two Checks) and
`staffe_minime_en.py` (EC2 §9.2.2 eq. 9.5N minimum stirrup ratio, EC2-style max spacing).
`bw,min`/`hw,min` are code-mandated fixed/threshold values, not formulas an engineer would derive
— cited by identity with a `nota` naming the rule, the same convention `relazione_sismica.py` uses
for table lookups (docs/architecture-phase2.md §6)."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura_minima_en import RHO_B_MIN_EN1998, ArmaturaMinimaEnResult
from .geometria_minima_en import (
    HW_MIN_MM_ALTO,
    HW_MIN_MM_BASSO,
    N_PIANI_SOGLIA_HW,
    GeometriaMinimaEnResult,
)
from .materiali import MaterialiResult
from .models import TraviCollegamentoInput
from .staffe_minime_en import PMAX_ASSOLUTO_MM_EC2, PMAX_FRAZIONE_D_EC2, RHO_MIN_COEFFICIENTE_EC2, StaffeMinimeEnResult

PI_GRECO = math.pi
CLAUSOLA_ARMATURA = "EN1998-1 §5.8.2(4)"
CLAUSOLA_GEOMETRIA = "EN1998-1 (Rif.Normativi)"
CLAUSOLA_STAFFE = "EC2 §9.2.2"


def traccia_armatura_minima_en(mat: MaterialiResult, arm: ArmaturaMinimaEnResult) -> Traccia:
    """2 passi: ρb, verifica (Check "Verifica armatura longitudinale minima")."""
    return Traccia(titolo="Armatura longitudinale minima (EN1998)", passi=(_passo_rho_b(mat, arm), _passo_verifica_armatura(mat, arm)))


def _passo_rho_b(mat: MaterialiResult, arm: ArmaturaMinimaEnResult) -> Passo:
    return Passo(
        simbolo="ρ_b", formula=f"{RHO_B_MIN_EN1998:g} * A_c",
        valori=(Valore(simbolo="A_c", valore=mat.ac_mm2, unita="mm2", descrizione="area della sezione di calcestruzzo, calcolata sopra"),),
        risultato=arm.rho_b_mm2, unita="mm2", clausola=CLAUSOLA_ARMATURA,
        nota=f"Area minima di armatura longitudinale ({RHO_B_MIN_EN1998 * 100:g}% di Ac).",
    )


def _passo_verifica_armatura(mat: MaterialiResult, arm: ArmaturaMinimaEnResult) -> Passo:
    soddisfatta = arm.verifica.passed
    return Passo(
        simbolo="A_s/ρ_b", formula="A_s > ρ_b",
        valori=(
            Valore(simbolo="A_s", valore=mat.as_mm2, unita="mm2", descrizione="area delle barre longitudinali presenti, calcolata sopra"),
            Valore(simbolo="ρ_b", valore=arm.rho_b_mm2, unita="mm2", descrizione="area minima richiesta, calcolata sopra"),
        ),
        risultato=mat.as_mm2, unita="mm2", clausola=arm.verifica.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Armatura longitudinale presente rispetto al minimo richiesto.",
    )


def traccia_geometria_minima_en(inputs: TraviCollegamentoInput, geom: GeometriaMinimaEnResult) -> Traccia:
    """4 passi: bw,min (lookup) + verifica base, hw,min (lookup/soglia) + verifica altezza."""
    return Traccia(
        titolo="Geometria minima di sezione (EN1998)",
        passi=(_passo_bw_min(geom), _passo_verifica_base(inputs, geom), _passo_hw_min(inputs, geom), _passo_verifica_altezza(inputs, geom)),
    )


def _passo_bw_min(geom: GeometriaMinimaEnResult) -> Passo:
    return Passo(
        simbolo="b_w,min", formula="b_w,min",
        valori=(Valore(simbolo="b_w,min", valore=geom.bw_min_mm, unita="mm", descrizione="base minima di normativa per travi di collegamento"),),
        risultato=geom.bw_min_mm, unita="mm", clausola=CLAUSOLA_GEOMETRIA,
        nota="Valore fisso di normativa, non dipendente dalla geometria della trave.",
    )


def _passo_verifica_base(inputs: TraviCollegamentoInput, geom: GeometriaMinimaEnResult) -> Passo:
    soddisfatta = geom.verifica_base.passed
    return Passo(
        simbolo="B/b_w,min", formula="B > b_w,min",
        valori=(
            Valore(simbolo="B", valore=inputs.b_mm, unita="mm", descrizione="base della sezione"),
            Valore(simbolo="b_w,min", valore=geom.bw_min_mm, unita="mm", descrizione="calcolato sopra"),
        ),
        risultato=inputs.b_mm, unita="mm", clausola=geom.verifica_base.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Base della sezione rispetto al minimo di normativa.",
    )


def _passo_hw_min(inputs: TraviCollegamentoInput, geom: GeometriaMinimaEnResult) -> Passo:
    assert inputs.n_piani is not None
    return Passo(
        simbolo="h_w,min", formula="h_w,min",
        valori=(
            Valore(
                simbolo="h_w,min", valore=geom.hw_min_mm, unita="mm",
                descrizione=f"N. piani={inputs.n_piani} {'≤' if inputs.n_piani <= N_PIANI_SOGLIA_HW else '>'} "
                            f"{N_PIANI_SOGLIA_HW}: soglia di normativa per il numero di piani",
            ),
        ),
        risultato=geom.hw_min_mm, unita="mm", clausola=CLAUSOLA_GEOMETRIA,
        nota=f"Altezza minima di normativa: {HW_MIN_MM_BASSO:g} mm se N.piani≤{N_PIANI_SOGLIA_HW}, altrimenti {HW_MIN_MM_ALTO:g} mm.",
    )


def _passo_verifica_altezza(inputs: TraviCollegamentoInput, geom: GeometriaMinimaEnResult) -> Passo:
    soddisfatta = geom.verifica_altezza.passed
    return Passo(
        simbolo="H/h_w,min", formula="H >= h_w,min",
        valori=(
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="h_w,min", valore=geom.hw_min_mm, unita="mm", descrizione="calcolato sopra"),
        ),
        risultato=inputs.h_mm, unita="mm", clausola=geom.verifica_altezza.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Altezza della sezione rispetto al minimo di normativa.",
    )


def traccia_staffe_minime_en(inputs: TraviCollegamentoInput, mat: MaterialiResult, staffe: StaffeMinimeEnResult) -> Traccia:
    """4 passi: d, pmax (informativo, EC2-style), ρ, verifica (Check "Verifica area staffe")."""
    return Traccia(
        titolo="Staffe minime (EN1998/EC2)",
        passi=(_passo_d(inputs, staffe), _passo_pmax(inputs, staffe), _passo_rho(inputs, staffe), _passo_verifica_staffe(mat, staffe)),
    )


def _passo_d(inputs: TraviCollegamentoInput, staffe: StaffeMinimeEnResult) -> Passo:
    return Passo(
        simbolo="d", formula="H - c",
        valori=(
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="c", valore=inputs.cf_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=staffe.d_mm, unita="mm",
        nota="Altezza utile della sezione.",
    )


def _passo_pmax(inputs: TraviCollegamentoInput, staffe: StaffeMinimeEnResult) -> Passo:
    assert inputs.alpha_staffa_deg is not None
    return Passo(
        simbolo="p_max", formula=f"min({PMAX_FRAZIONE_D_EC2:g} * d * (1 + 1 / tan(α)), {PMAX_ASSOLUTO_MM_EC2:g})",
        valori=(
            Valore(simbolo="d", valore=staffe.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="α", valore=inputs.alpha_staffa_deg, unita="°", descrizione="inclinazione delle staffe rispetto all'asse della trave"),
        ),
        risultato=staffe.pmax_mm, unita="mm", clausola=CLAUSOLA_STAFFE,
        nota="Passo massimo ammesso delle staffe (regola EC2). Valore informativo: nessun Check di "
             "questo foglio lo confronta con il passo p effettivamente adottato.",
    )


def _passo_rho(inputs: TraviCollegamentoInput, staffe: StaffeMinimeEnResult) -> Passo:
    return Passo(
        simbolo="ρ", formula="π * φ_st^2 / 4 * n_br / (B * p)",
        valori=(
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ_st", valore=inputs.phi_staffa_mm, unita="mm", descrizione="diametro delle staffe"),
            Valore(simbolo="n_br", valore=float(inputs.n_bracci), descrizione="numero di bracci delle staffe"),
            Valore(simbolo="B", valore=inputs.b_mm, unita="mm", descrizione="base della sezione"),
            Valore(simbolo="p", valore=inputs.p_mm, unita="mm", descrizione="passo staffe considerato"),
        ),
        risultato=staffe.rho, unita="-",
        nota="Percentuale di armatura a taglio (staffe) presente.",
    )


def _passo_verifica_staffe(mat: MaterialiResult, staffe: StaffeMinimeEnResult) -> Passo:
    soddisfatta = staffe.verifica.passed
    return Passo(
        simbolo="ρ_min", formula=f"{RHO_MIN_COEFFICIENTE_EC2:g} * sqrt(f_ck) / f_yk < ρ",
        valori=(
            Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione="resistenza caratteristica cilindrica del calcestruzzo, calcolata sopra"),
            Valore(simbolo="f_yk", valore=mat.fyk_MPa, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio, calcolata sopra"),
            Valore(simbolo="ρ", valore=staffe.rho, descrizione="percentuale di armatura a staffe presente, calcolata sopra"),
        ),
        risultato=staffe.rho_min, unita="-", clausola=staffe.verifica.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Percentuale minima di armatura a taglio (staffe), EC2 §9.2.2 eq. 9.5N — usa fyk, non fyd "
             "(review finding: il foglio nomina la tabella 'fyd' ma legge la colonna fyk).",
    )

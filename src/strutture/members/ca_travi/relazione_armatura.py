"""Verified restatement (docs/architecture-phase2.md) of the reinforcement-limit checks:
`Check`s 1-4 (`armatura_limiti.area_minima_tesa_mm2`/`limiti_staffe`, NTC2018 §4.1.6.1.1) and
`Check`s 5-7 (`armatura_limiti.duttilita_longitudinale_sismica`, NTC2018 §7.4.6.2.1). Each step
combines the limit's own formula with the comparison it drives (one `Passo` = one `Check`),
mirroring `ca_taglio_non_armato.relazione._passo_verifica_rho_l`. Standard mode only (this
module is never called with `legacy_compat=True`, see `strutture.shared.tool._con_relazione`),
so the fixed-mode branches of `armatura_limiti.py` apply throughout.

`A_s,1`, the tension steel of the FIRST layer alone (not `A_s`, which includes the second layer),
is the quantity NTC2018 §7.4.6.2.1's ductility ratios are actually checked against
(`armatura_limiti.duttilita_longitudinale_sismica`'s `as_tesa_mm2`); it is not exposed by
`ArmaturaLimitiOutput`, so it is read straight from the package's own `bars_area` call, exactly
as the architecture brief allows.
"""
from strutture.shared.rebar_catalog import bars_area
from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura_limiti import (
    AS_MAX_RHO,
    AS_MIN_RHO_ASSOLUTO,
    AS_MIN_RHO_FCTM,
    AST_MIN_LEGACY_COEFF,
    MM2_PER_M2,
    PASSO_MAX_ASSOLUTO_MM,
    PASSO_MAX_RAPPORTO_D,
    RAPPORTO_ARMATURA_COMPRESSA_MIN,
    RHO_MAX_SISMICO_ADDENDO,
    RHO_MIN_SISMICO_NUMERATORE,
    RHO_W_MIN_COEFF,
)
from .models import ClasseDuttilita, TraveRettangolareInput, TraveRettangolareOutput

PASSO_MAX_LEGACY_TESTO = "1000/3"  # armatura_limiti.PASSO_MAX_LEGACY_MM, esatto come frazione
ASW_MIN_CLAUSE = "NTC2018 §4.1.6.1.1 + EN 1992-1-1 §9.2.2(5)"  # review finding (WRONG_CLAUSE): il
# secondo termine del max (rho_w,min*b*1000) è EC2 9.2.2(5), non NTC2018 (che impone solo 1,5*b).


def traccia_limiti_armatura(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """4 passi, uno per ciascuno dei 4 Check di NTC2018 §4.1.6.1.1."""
    return Traccia(
        titolo="Limiti di armatura longitudinale e trasversale",
        passi=(
            _passo_as_min(inputs, output), _passo_as_max(inputs, output),
            _passo_asw_min(inputs, output), _passo_passo_max(inputs, output),
        ),
    )


def traccia_duttilita_sismica(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """3 passi, uno per ciascuno dei 3 Check di NTC2018 §7.4.6.2.1."""
    as_1_mm2 = bars_area(inputs.n_ferri1, inputs.diametro_ferri1_mm)
    return Traccia(
        titolo="Duttilità longitudinale sismica",
        passi=(_passo_rho_min(inputs, output, as_1_mm2), _passo_rho_max(inputs, output, as_1_mm2), _passo_as_comp_min(inputs, output, as_1_mm2)),
    )


def _passo_as_min(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    armatura, materiali = output.armatura, output.materiali
    soddisfatta = armatura.as_min_mm2 <= armatura.as_o_mm2
    return Passo(
        simbolo="A_s,min",
        formula=f"max({AS_MIN_RHO_ASSOLUTO:g} * b * d, {AS_MIN_RHO_FCTM:g} * b * d * f_ctm / f_yk) <= A_s",
        valori=(
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="base della trave"),
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm", descrizione="altezza utile"),
            Valore(simbolo="f_ctm", valore=materiali.calcestruzzo.fctm_MPa, unita="MPa", descrizione="resistenza media a trazione del calcestruzzo"),
            Valore(simbolo="f_yk", valore=materiali.acciaio.fyk_MPa, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio"),
            Valore(simbolo="A_s", valore=armatura.as_o_mm2, unita="mm²", descrizione="armatura tesa presente"),
        ),
        risultato=armatura.as_min_mm2, unita="mm²", clausola="NTC2018 §4.1.6.1.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
    )


def _passo_as_max(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    armatura = output.armatura
    soddisfatta = armatura.as_o_mm2 <= armatura.as_max_mm2
    return Passo(
        simbolo="A_s,max",
        formula=f"{AS_MAX_RHO:g} * b * h >= A_s",
        valori=(
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="A_s", valore=armatura.as_o_mm2, unita="mm²"),
        ),
        risultato=armatura.as_max_mm2, unita="mm²", clausola="NTC2018 §4.1.6.1.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Armatura massima tesa, 4% dell'area lorda della sezione.",
    )


def _passo_asw_min(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    armatura, fck_MPa = output.armatura, output.materiali.calcestruzzo.fck_MPa
    soddisfatta = armatura.ast_min_per_m_mm2 <= armatura.asw_per_m_mm2
    return Passo(
        simbolo="A_sw,min",
        formula=f"max({AST_MIN_LEGACY_COEFF:g} * b, {RHO_W_MIN_COEFF:g} * sqrt(f_ck) / f_yk * b * {MM2_PER_M2:g}) <= A_sw",
        valori=(
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica del calcestruzzo"),
            Valore(simbolo="f_yk", valore=output.materiali.acciaio.fyk_MPa, unita="MPa"),
            Valore(simbolo="A_sw", valore=armatura.asw_per_m_mm2, unita="mm²/m"),
        ),
        risultato=armatura.ast_min_per_m_mm2, unita="mm²/m", clausola=ASW_MIN_CLAUSE,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Il floor NTC2018 Ast=1,5·b si somma, come massimo, al floor EC2 9.2.2(5) ρw,min·b.",
    )


def _passo_passo_max(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    armatura = output.armatura
    soddisfatta = inputs.passo_staffe1_mm <= armatura.passo_max_staffe_mm
    return Passo(
        simbolo="s_max",
        formula=f"min({PASSO_MAX_ASSOLUTO_MM:g}, {PASSO_MAX_LEGACY_TESTO}, {PASSO_MAX_RAPPORTO_D:g} * d) >= s_1",
        valori=(
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),
            Valore(simbolo="s_1", valore=inputs.passo_staffe1_mm, unita="mm", descrizione="passo delle staffe, primo tratto"),
        ),
        risultato=armatura.passo_max_staffe_mm, unita="mm", clausola="NTC2018 §4.1.6.1.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Passo massimo ammesso delle staffe: tetto assoluto di 330 mm (NTC2018 §4.1.6.1.1), sempre "
             "più restrittivo del limite equivalente di tre staffe al metro (1000/3 mm, stessa clausola) "
             "— quest'ultimo termine non può quindi mai governare da solo, è mantenuto per completezza.",
    )


def _passo_rho_min(inputs: TraveRettangolareInput, output: TraveRettangolareOutput, as_1_mm2: float) -> Passo:
    armatura, fyk_MPa = output.armatura, output.materiali.acciaio.fyk_MPa
    soddisfatta = armatura.rho_min_sismico <= armatura.rho_tesa
    return Passo(
        simbolo="ρ_min",
        formula=f"{RHO_MIN_SISMICO_NUMERATORE:g} / f_yk <= A_s,1 / (b * d)",
        valori=(
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa"),
            Valore(simbolo="A_s,1", valore=as_1_mm2, unita="mm²", descrizione="armatura tesa del solo primo strato di ferri"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),
        ),
        risultato=armatura.rho_min_sismico, unita="-", clausola="NTC2018 §7.4.6.2.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Percentuale minima di armatura tesa in zona critica (duttilità sismica).",
    )


def _passo_rho_max(inputs: TraveRettangolareInput, output: TraveRettangolareOutput, as_1_mm2: float) -> Passo:
    armatura, fyk_MPa = output.armatura, output.materiali.acciaio.fyk_MPa
    soddisfatta = armatura.rho_tesa <= armatura.rho_max_sismico
    return Passo(
        simbolo="ρ_max",
        formula=f"A_s' / (b * d) + {RHO_MAX_SISMICO_ADDENDO:g} / f_yk >= A_s,1 / (b * d)",
        valori=(
            Valore(simbolo="A_s'", valore=armatura.as_comp_mm2, unita="mm²", descrizione="armatura compressa presente"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa"),
            Valore(simbolo="A_s,1", valore=as_1_mm2, unita="mm²"),
        ),
        risultato=armatura.rho_max_sismico, unita="-", clausola="NTC2018 §7.4.6.2.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
    )


def _passo_as_comp_min(inputs: TraveRettangolareInput, output: TraveRettangolareOutput, as_1_mm2: float) -> Passo:
    armatura = output.armatura
    classe: ClasseDuttilita = inputs.classe_duttilita
    coeff = RAPPORTO_ARMATURA_COMPRESSA_MIN[classe]
    soddisfatta = armatura.as_comp_min_sismico_mm2 <= armatura.as_comp_mm2
    return Passo(
        simbolo="A_s',min",
        formula=f"{coeff:g} * A_s,1 <= A_s'",
        valori=(
            Valore(simbolo="A_s,1", valore=as_1_mm2, unita="mm²", descrizione="armatura tesa del solo primo strato di ferri"),
            Valore(simbolo="A_s'", valore=armatura.as_comp_mm2, unita="mm²"),
        ),
        risultato=armatura.as_comp_min_sismico_mm2, unita="mm²", clausola="NTC2018 §7.4.6.2.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Il coefficiente ({coeff:g}) dipende dalla classe di duttilità: 0,5 per CD\"A\", 0,25 per CD\"B\" (qui {classe}).",
    )

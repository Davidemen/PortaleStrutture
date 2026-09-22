"""Verified restatement (docs/architecture-phase2.md) of `armatura_minima.py` (NTC2018 §7.4.6.2.1 /
EC8 5.4.3.2.2, rows CX25:DA27): minimum longitudinal steel area A_s,min (`Check` "Area minima di
armatura longitudinale") and the geometric ratio envelope ρ_s (`Check` "Percentuale di armatura
longitudinale"). Both formulas are norma-dependent through `regole.resolve` (architecture-batch2.md
§3); `legacy_compat=False` throughout (`relazione` never runs in Excel mode, docs/architecture-
phase2.md §1), so only the code-standard branch of each `RuleSet` is ever restated here."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura_minima import AC_RATIO_CEILING, AC_RATIO_FLOOR, NED_OVER_FYD_RATIO, RS_MAX
from .models import Norma, PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .regole import RuleSet, resolve

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput

_CLAUSOLA_AS_MIN: dict[Norma, str] = {
    "NTC2018": "NTC2018 §4.1.6.1.2 + §7.4.6.2.2",
    "EC2": "EN 1992-1-1 §9.5.2(2) + Allegato Nazionale italiano",
}


def traccia_limiti_armatura(inputs: PilastroInput, output: PilastroOutput) -> Traccia:
    """2 o 3 passi: A_s,min (Check "Area minima di armatura longitudinale"), il tetto ρ_s<4% (Check
    "Percentuale di armatura longitudinale") e, solo quando la normativa selezionata lo prevede
    (NTC2018 codice), il pavimento ρ_s>=ρ_s,min dello stesso Check (§7.4.6.2.1: il foglio NTC2018
    abbandona questo secondo confronto, mantenendo solo il tetto — vedi `regole.py`)."""
    rules = resolve(inputs.norma, legacy_compat=False)
    passi = (_passo_as_min(inputs, output, rules), _passo_rho_s_max(inputs, output))
    if rules.rs_controlla_minimo:
        passi = (*passi, _passo_rho_s_min(inputs, output))
    return Traccia(titolo="Limiti di armatura longitudinale", passi=passi)


def _passo_as_min(inputs: PilastroInput, output: PilastroOutput, rules: RuleSet) -> Passo:
    """Review finding (MISLEADING): la formula ristata applicava anche in ramo NTC2018 un
    `min(..., 0,04*A_c)` esterno all'inviluppo per massimo — NTC2018 §4.1.6.1.2 non prevede quel
    tetto (che è invece la MASSIMA armatura ammessa, §7.4.6.2.2, già verificata a parte dal Check
    "Percentuale di armatura longitudinale" / passo ρ_s sopra): un lettore che segue la formula
    stampata leggerebbe "serve più acciaio del massimo consentito" come "va bene". Il tetto non è
    mai attivo per i casi di prova (richiederebbe N_Ed > 0,4·A_c·f_yd), quindi il valore numerico
    resta quello calcolato dal codice (`armatura_minima.armatura_minima`, non modificato) — solo la
    formula ristata non lo applica più."""
    armatura = output.armatura_minima
    ratio = rules.as_min_area_ratio
    formula = f"max({ratio:g} * A_c, {NED_OVER_FYD_RATIO:g} * N_Ed * 1000 / f_yd) <= A_s"
    if rules.as_min_combinatore == "max":
        nota = "Inviluppo per massimo, senza tetto: formula propria del ramo EC2 (0,3% qui, per effetto dell'Allegato Nazionale italiano)."
    else:
        nota = ("Inviluppo per massimo (area minima assoluta, quota proporzionale a N_Ed); il tetto del 4% di A_c "
                "è la percentuale massima ammessa, verificata a parte (Check \"Percentuale di armatura longitudinale\").")
    soddisfatta = armatura.as_min_mm2 <= output.geometria.as_mm2
    return Passo(
        simbolo="A_s,min", formula=formula,
        valori=(
            Valore(simbolo="A_c", valore=output.geometria.ac_mm2, unita="mm2"),
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa"),
            Valore(simbolo="A_s", valore=output.geometria.as_mm2, unita="mm2", descrizione="armatura longitudinale presente"),
        ),
        risultato=armatura.as_min_mm2, unita="mm2", clausola=_CLAUSOLA_AS_MIN[inputs.norma],
        esito="soddisfatta" if soddisfatta else "non soddisfatta", nota=nota,
    )


def _passo_rho_s_max(inputs: PilastroInput, output: PilastroOutput) -> Passo:
    armatura = output.geometria
    soddisfatta = armatura.rs < RS_MAX
    return Passo(
        simbolo="ρ_s", formula=f"A_s / A_c < {RS_MAX:g}",
        valori=(
            Valore(simbolo="A_s", valore=armatura.as_mm2, unita="mm2"),
            Valore(simbolo="A_c", valore=armatura.ac_mm2, unita="mm2"),
        ),
        risultato=armatura.rs, unita="-", clausola="NTC2018 §7.4.6.2.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tetto massimo alla percentuale geometrica di armatura longitudinale in CD \"B\" (4%).",
    )


def _passo_rho_s_min(inputs: PilastroInput, output: PilastroOutput) -> Passo:
    armatura, geometria = output.armatura_minima, output.geometria
    soddisfatta = armatura.rs_min <= geometria.rs
    return Passo(
        simbolo="ρ_s,min",
        formula=f"max({AC_RATIO_FLOOR:g} * A_c, {NED_OVER_FYD_RATIO:g} * N_Ed * 1000 / f_yd, {AC_RATIO_CEILING:g} * A_c) / A_c <= A_s / A_c",
        valori=(
            Valore(simbolo="A_c", valore=geometria.ac_mm2, unita="mm2"),
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa"),
            Valore(simbolo="A_s", valore=geometria.as_mm2, unita="mm2"),
        ),
        risultato=armatura.rs_min, unita="-", clausola="NTC2018 §7.4.6.2.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Percentuale minima di armatura longitudinale (inviluppo a tre candidati, coefficiente NTC "
             "fisso indipendentemente dalla normativa selezionata — vedi armatura_minima.py).",
    )

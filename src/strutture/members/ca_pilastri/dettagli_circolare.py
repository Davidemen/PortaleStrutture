"""`_dettagli` di pilastro-circolare, estratta da tool_circolare.py e spezzata in funzioni piu'
piccole per restare entro il limite di 40 righe per funzione (regola dura 12 di CLAUDE.md).
Comportamento identico all'originale: nessuna logica nuova."""
from strutture.shared.divergences import legacy
from strutture.shared.report import Check

from .dettagli import (
    diametro_staffe_minimo_mm,
    interasse_ferri_verticali_mm,
    interasse_staffe_massimo_mm,
    perimetro_circolare_mm,
)
from .models import DettagliResult, PilastroCircolareInput
from .regole import RuleSet

AREA_MASSIMA_RATIO = 0.04  # EC2 §9.5.2(3) — riga "Area massima barre long." dedicata


def _dettagli_soglie(inputs: PilastroCircolareInput, rules: RuleSet) -> tuple[float, float, float]:
    perimetro_mm = perimetro_circolare_mm(inputs.d_mm, inputs.c_mm)  # formula corretta per il cerchio (nessun bug qui)
    interasse_calc = interasse_ferri_verticali_mm(perimetro_mm, inputs.n_ferri)
    soglia_staffe = diametro_staffe_minimo_mm(inputs.diametro_ferri_mm, legacy_compat=inputs.legacy_compat, combinatore=rules.staffe_diametro_combinatore)
    dimensione_min_mm = inputs.d_mm if rules.staffe_min_dimensione else None
    soglia_interasse_staffe = interasse_staffe_massimo_mm(
        inputs.diametro_ferri_mm, bar_multiplier=rules.staffe_bar_multiplier, fixed_mm=rules.staffe_fixed_mm,
        dimensione_min_mm=dimensione_min_mm,
    )
    return interasse_calc, soglia_staffe, soglia_interasse_staffe


def _dettagli_flag(inputs: PilastroCircolareInput, rules: RuleSet, soglia_staffe: float, as_min_mm2: float, as_mm2: float) -> tuple[bool, bool, bool]:
    diam_long_ok = (
        inputs.diametro_ferri_mm > rules.diametro_long_min_mm
        if legacy("ca-pilastri/limite-diametro-barre-longitudinali-stretto", inputs.legacy_compat)
        else inputs.diametro_ferri_mm >= rules.diametro_long_min_mm
    )
    area_min_ok = (
        as_min_mm2 < as_mm2
        if legacy("ca-pilastri/limite-area-minima-longitudinale-stretto", inputs.legacy_compat)
        else as_min_mm2 <= as_mm2
    )
    diam_staffe_ok = (
        soglia_staffe < inputs.diametro_staffe_mm
        if legacy("ca-pilastri/limite-diametro-staffe-stretto", inputs.legacy_compat)
        else soglia_staffe <= inputs.diametro_staffe_mm
    )
    return diam_long_ok, area_min_ok, diam_staffe_ok


def _dettagli(inputs: PilastroCircolareInput, rules: RuleSet, ac_mm2: float, as_min_mm2: float, as_mm2: float) -> tuple[DettagliResult, tuple[Check, ...]]:
    interasse_calc, soglia_staffe, soglia_interasse_staffe = _dettagli_soglie(inputs, rules)
    diam_long_ok, area_min_ok, diam_staffe_ok = _dettagli_flag(inputs, rules, soglia_staffe, as_min_mm2, as_mm2)
    result = DettagliResult(
        diametro_long_min_mm=rules.diametro_long_min_mm, interasse_long_max_mm=rules.long_bar_max_spacing_mm,
        interasse_long_calcolato_mm=interasse_calc, as_long_min_mm2=as_min_mm2,
        diametro_staffe_min_mm=soglia_staffe, interasse_staffe_max_mm=soglia_interasse_staffe,
    )
    checks = (
        Check(name="Diametro minimo delle barre longitudinali", passed=diam_long_ok, clause="NTC2018 §4.1.6.1.2"),
        Check(name="Interasse massimo delle barre longitudinali", passed=interasse_calc <= rules.long_bar_max_spacing_mm, clause="NTC2018 §7.4.6.2.2"),
        Check(name="Area minima di armatura longitudinale", passed=area_min_ok, clause="NTC2018 §7.4.6.2.2"),
        Check(name="Diametro minimo delle staffe", passed=diam_staffe_ok, clause="NTC2018 §4.1.6.1.2"),
        Check(name="Interasse massimo delle staffe", passed=inputs.passo_staffe_mm <= soglia_interasse_staffe, clause="NTC2018 §4.1.6.1.2"),
    )
    if rules.as_max_check:
        as_max_mm2 = AREA_MASSIMA_RATIO * ac_mm2
        checks = (*checks, Check(name="Area massima di armatura longitudinale", passed=as_mm2 <= as_max_mm2, clause="EC2 §9.5.2(3)",
                                  value=as_mm2, limit=as_max_mm2, unit="mm2"))
    return result, checks

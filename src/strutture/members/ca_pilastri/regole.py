"""Per-norm rule dispatch table (architecture-batch2.md §3): one frozen `RuleSet` per
`(norma, legacy_compat)` pair. `tool_rettangolare.py`/`tool_circolare.py` resolve it once and pass
explicit keyword parameters to the (mostly norm-agnostic) step modules — no `if norma == ...`
scattered through the steps themselves.

`legacy_compat=True` reproduces that norm's OWN workbook (NTC2008 → `ca-pilastri`, NTC2018 →
`ca-pilastri-ntc2018`, EC2 → `ca-pilastri-ec2`); `legacy_compat=False` is the norm's own text.
`(NTC2008, False)` has no maintained code-standard branch (a superseded norm) — `resolve` raises
`CalcError`.
"""
from dataclasses import dataclass
from typing import Literal

from strutture.shared.report import CalcError

from .dettagli import LONG_BAR_MAX_SPACING_MM, LONG_BAR_MAX_SPACING_SEISMIC_MM
from .models import Norma

LambdaLimKind = Literal["ntc", "ec2"]  # which module computes λlim: snellezza.py or limiti_ec2.py
RaggioInerzia = Literal["netto", "lordo"]
AsMinCombinatore = Literal["auto", "max"]


@dataclass(frozen=True)
class RuleSet:
    """One row of the dispatch table. Every field is a plain value or small literal — no
    behaviour lives here, only the parameters the steps already accept as keyword arguments."""

    lambda_lim_kind: LambdaLimKind
    lambda_lim_unit_fix: bool  # "ntc" kind only: False reproduces the NTC2008 sheet's missing-×1000 bug under legacy_compat=True
    raggio_inerzia: RaggioInerzia
    nu1_ec2: bool  # True -> ν1 = 0.6*(1-fck/250) (EC2 §6.2.2(6)); False -> fixed 0.5 (NTC)
    diametro_long_min_mm: float
    staffe_bar_multiplier: float
    staffe_fixed_mm: float
    staffe_min_dimensione: bool  # True -> add the column's smaller side as a 3rd spacing candidate (EC2 §9.5.3(3))
    staffe_diametro_combinatore: AsMinCombinatore  # "auto" = legacy MIN / code-standard MAX (today's behaviour); "max" = always MAX (EC2's own formula)
    as_min_area_ratio: float
    as_min_combinatore: AsMinCombinatore
    rs_controlla_minimo: bool  # False -> "percentuale_armatura" only checks the 4% ceiling (NTC2018/EC2 sheets)
    as_max_check: bool  # True -> add a standalone "area_massima_longitudinale" detailing check (EC2)
    a_fisso: float | None  # EC2 slenderness coefficient A; None -> derive from phi_ef (default 0.7)
    c_fisso: float | None  # EC2 slenderness coefficient C; None -> derive as 1.7-rm
    long_bar_max_spacing_mm: float  # "interasse_massimo_longitudinale" (§7.4.6.2.2 seismic 250mm vs the sheet's own non-seismic 300mm)


_NTC2008_LEGACY = RuleSet(
    lambda_lim_kind="ntc", lambda_lim_unit_fix=False, raggio_inerzia="netto", nu1_ec2=False,
    diametro_long_min_mm=12.0, staffe_bar_multiplier=12.0, staffe_fixed_mm=250.0,
    staffe_min_dimensione=False, staffe_diametro_combinatore="auto",
    as_min_area_ratio=0.003, as_min_combinatore="auto", rs_controlla_minimo=True,
    as_max_check=False, a_fisso=None, c_fisso=None, long_bar_max_spacing_mm=LONG_BAR_MAX_SPACING_MM,
)
_NTC2018_LEGACY = RuleSet(
    lambda_lim_kind="ntc", lambda_lim_unit_fix=True, raggio_inerzia="lordo", nu1_ec2=False,
    diametro_long_min_mm=12.0, staffe_bar_multiplier=12.0, staffe_fixed_mm=250.0,
    staffe_min_dimensione=False, staffe_diametro_combinatore="auto",
    as_min_area_ratio=0.003, as_min_combinatore="auto", rs_controlla_minimo=False,
    as_max_check=False, a_fisso=None, c_fisso=None, long_bar_max_spacing_mm=LONG_BAR_MAX_SPACING_MM,
)
_NTC2018_CODICE = RuleSet(
    lambda_lim_kind="ntc", lambda_lim_unit_fix=True, raggio_inerzia="lordo", nu1_ec2=False,
    diametro_long_min_mm=12.0, staffe_bar_multiplier=12.0, staffe_fixed_mm=250.0,
    staffe_min_dimensione=False, staffe_diametro_combinatore="auto",
    as_min_area_ratio=0.003, as_min_combinatore="auto", rs_controlla_minimo=True,
    as_max_check=False, a_fisso=None, c_fisso=None, long_bar_max_spacing_mm=LONG_BAR_MAX_SPACING_SEISMIC_MM,
)
_EC2_LEGACY = RuleSet(
    # NB: the EC2 sheet's own "Raggio d'inerzia" formula is `SQRT(((MIN(H6:I7))^3*(MAX(H6:I7))/12)/(H6*H7))`
    # (rect) / `SQRT((PI()*H6^4/64)/(PI()*H6^2/4))` (circ) — the SAME gross-section formula as the
    # NTC2018 sheet (both give i=115.47/100 on the golden cases), confirmed directly against
    # `build/cellmaps/ca-pilastri-ec2/`; docs/specs/ca-pilastri-ec2.md's prose calling this
    # "unchanged, net/core-section" for the rectangular case does not match the workbook formula.
    lambda_lim_kind="ec2", lambda_lim_unit_fix=True, raggio_inerzia="lordo", nu1_ec2=True,
    diametro_long_min_mm=8.0, staffe_bar_multiplier=20.0, staffe_fixed_mm=400.0,
    staffe_min_dimensione=True, staffe_diametro_combinatore="max",
    as_min_area_ratio=0.002, as_min_combinatore="max", rs_controlla_minimo=False,
    as_max_check=True, a_fisso=0.7, c_fisso=0.7, long_bar_max_spacing_mm=LONG_BAR_MAX_SPACING_MM,
)
_EC2_CODICE = RuleSet(
    lambda_lim_kind="ec2", lambda_lim_unit_fix=True, raggio_inerzia="lordo", nu1_ec2=True,
    diametro_long_min_mm=8.0, staffe_bar_multiplier=20.0, staffe_fixed_mm=400.0,
    staffe_min_dimensione=True, staffe_diametro_combinatore="max",
    # EN 1992-1-1 §9.5.2(2) gives 0.002*Ac as the RECOMMENDED value, but this tool declares EC2
    # WITH the Italian National Annex (models.py _NORMA_DESCRIPTION, alpha_cc=0.85 applied in
    # materiali.py); the Italian NA raises the column minimum to 0.003*Ac (aligned with NTC2018
    # §4.1.6.1.2) — review finding (HIGH). 0.002 stays under legacy_compat=True (that sheet's own
    # value, `_EC2_LEGACY` below).
    as_min_area_ratio=0.003, as_min_combinatore="max", rs_controlla_minimo=False,
    as_max_check=True, a_fisso=None, c_fisso=None, long_bar_max_spacing_mm=LONG_BAR_MAX_SPACING_SEISMIC_MM,
)

RULES: dict[tuple[Norma, bool], RuleSet] = {
    ("NTC2008", True): _NTC2008_LEGACY,
    ("NTC2018", True): _NTC2018_LEGACY,
    ("NTC2018", False): _NTC2018_CODICE,
    ("EC2", True): _EC2_LEGACY,
    ("EC2", False): _EC2_CODICE,
}


def resolve(norma: Norma, legacy_compat: bool) -> RuleSet:
    """Look up the `RuleSet` for this `(norma, legacy_compat)` pair; `CalcError` when there is no
    maintained combination (NTC2008 has no code-standard branch — see module docstring)."""
    rules = RULES.get((norma, legacy_compat))
    if rules is None:
        raise CalcError(
            "NTC 2008: disponibile solo come riproduzione del foglio Excel originale "
            "(impostare legacy_compat=True), non come normativa di calcolo corrente."
        )
    return rules

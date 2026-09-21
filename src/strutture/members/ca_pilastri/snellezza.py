"""Step: slenderness check, NTC2018 §4.1.6.1.3 / EC2 5.8.3.1, rows J53-J57 (rett.) / J60-J64 (circ.).

CRITICAL fix: the NTC2008 sheet's λlim (`25/SQRT(Ned/(Ac*fcd))`) compares Ned in kN directly
against Ac*fcd in N, omitting a ×1000 conversion — overstating λlim by ~31× (confirmed
non-conservative, see docs/divergences/ca-pilastri.md). The NTC2018 sheet fixes the ×1000 bug but
keeps the same "25/√ν" formula (`unit_fix=True` below); the NTC2018 code-standard formula is the
"real" clause NTC2018 §4.1.2.3.9.2: λlim = 15.4*C/√ν, C = 1.7-rm. EC2's own λlim formula (20*A*B*C/√n)
lives in `limiti_ec2.py` — it needs the mechanical reinforcement ratio ω, not just Ac/fcd/Ned.

The sheet also computes the radius of gyration `i` on the net (cover-reduced) section rather than
the gross Ac under NTC2008/EC2 `legacy_compat=True`; kept as `legacy_compat` behaviour (architecture
D3 / architecture-batch2.md §3) while every code-standard path, and the NTC2018 legacy sheet itself
(§4 delta), use `shared.section_geometry`'s gross-section radius of gyration — see `regole.py`.
"""
import math

from strutture.shared.divergences import legacy
from strutture.shared.units import kn_to_n

LAMBDA_LIM_COEFFICIENT_LEGACY = 25.0  # J53/J60, provenienza non documentata nel foglio (NTC2008/NTC2018)
LAMBDA_LIM_COEFFICIENT = 15.4  # NTC2018 §4.1.2.3.9.2 ≈ 20*A*B (A=0.7, B=1.1 valori tipici)
END_MOMENT_RATIO_BASE = 1.7  # NTC2018 §4.1.2.3.9.2 — C = 1.7 - rm
RM_UNKNOWN_DEFAULT = 1.0  # rm "non noto": NTC2018 §4.1.2.3.9.2 / EN 1992-1-1 §5.8.3.1(1) nota 3 -> C=0.7
L0_HARDCODED_LEGACY_MM = 3000.0  # J54 nel foglio NTC2008 originale, indipendente da H


def coefficiente_c(rm: float | None) -> float:
    """C (NTC2018 §4.1.2.3.9.2 / EN 1992-1-1 §5.8.3.1(1) nota 3): C = 1.7 - rm quando rm è noto.
    Quando rm non è noto (default `None`), per elementi non controventati, o quando i momenti del
    primo ordine derivano prevalentemente da imperfezioni o da un carico trasversale, la norma
    prescrive C = 0.7 — equivalente a rm = 1 (singola curvatura), NON rm = 0 (che darebbe C = 1.7,
    il bug corretto da questa funzione: vedi docs/divergences/ca-pilastri.md)."""
    rm_effettivo = RM_UNKNOWN_DEFAULT if rm is None else rm
    return END_MOMENT_RATIO_BASE - rm_effettivo


def l0_effettivo_mm(l0_mm: float | None, h_mm: float, *, legacy_compat: bool, hardcode_mm: float | None = L0_HARDCODED_LEGACY_MM) -> float:
    """J54: se l0 non è specificato, il foglio NTC2008 usava un valore fisso di 3000mm indipendente
    dall'altezza netta H (`hardcode_mm`, non-None solo per quel foglio); il valore corretto — e
    quello del foglio NTC2018/EC2, che già usa l0=H·β con β=1 — è l'altezza netta stessa. Vedi
    docs/divergences/ca-pilastri.md."""
    if l0_mm is not None:
        return l0_mm
    if legacy("ca-pilastri/l0-fisso-3000mm", legacy_compat) and hardcode_mm is not None:
        return hardcode_mm
    return h_mm


def lambda_limite(ned_kN: float, ac_mm2: float, fcd_MPa: float, *, rm: float | None = None, legacy_compat: bool, unit_fix: bool = False) -> float:
    """`unit_fix=False` (default) reproduces the NTC2008 sheet's own λlim bug when `legacy_compat`
    is True (today's behaviour, unchanged); `unit_fix=True` selects the NTC2018 sheet's own
    (already-fixed) "25/√ν" formula instead. `legacy_compat=False` always uses the NTC2018
    code-standard formula (15.4*C/√ν, C = `coefficiente_c(rm)`), independent of `unit_fix`."""
    # unit_fix=True (NTC2018 sheet) reproduces ca-pilastri/lambda-lim-ntc2018-foglio-non-normativo
    # with the same branch (ramo="nessuno" in the register: no separate legacy() call for it).
    if legacy("ca-pilastri/lambda-lim-manca-conversione-kn", legacy_compat):
        nu_kn_or_n = kn_to_n(ned_kN) if unit_fix else ned_kN
        return LAMBDA_LIM_COEFFICIENT_LEGACY / math.sqrt(nu_kn_or_n / (ac_mm2 * fcd_MPa))
    nu = kn_to_n(ned_kN) / (ac_mm2 * fcd_MPa)
    c = coefficiente_c(rm)
    return LAMBDA_LIM_COEFFICIENT * c / math.sqrt(nu)


def raggio_inerzia_netto_rettangolare_mm(l1_mm: float, l2_mm: float, c_mm: float) -> float:
    """J55 (legacy): raggio d'inerzia sulla sezione netta (ridotta di 2·copriferro su ogni lato)."""
    lmin, lmax = min(l1_mm, l2_mm), max(l1_mm, l2_mm)
    return math.sqrt(((lmin - 2 * c_mm) ** 3 * (lmax - 2 * c_mm) / 12.0) / ((l1_mm - 2 * c_mm) * (l2_mm - 2 * c_mm)))


def raggio_inerzia_netto_circolare_mm(d_mm: float, c_mm: float) -> float:
    """J62 (legacy)."""
    d_netto_mm = d_mm - 2 * c_mm
    return math.sqrt((math.pi * d_netto_mm**4 / 64.0) / (math.pi * d_netto_mm**2 / 4.0))


def snellezza(l0_mm: float, i_mm: float) -> float:
    return l0_mm / i_mm


def verifica_snellezza(lambda_: float, lambda_lim: float) -> bool:
    return lambda_ < lambda_lim

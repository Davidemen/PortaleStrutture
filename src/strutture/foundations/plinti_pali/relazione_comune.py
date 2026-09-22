"""Constants and small `Valore` builders shared by every `relazione_*.py` module of this package
(docs/architecture-phase2.md §6). STANDARD mode only throughout (`legacy_compat=False`,
`execute()` never calls `relazione` otherwise): every formula restated here is the fixed branch of
`flessione.py` / `puntoni_tiranti.py` / `taglio_punzonamento.py`, never the sheet reproduction.

CALCULATION FINDING (report only, code untouched): `materiali.py::materiali()` builds
`ConcreteProperties.fcd_MPa` via `concrete_properties(classe_calcestruzzo, legacy_compat=False)`,
which never receives `gamma_c` and so always uses the SHARED module's own default (1,5) — unlike
every actual design step (`flessione`, `puntoni_tiranti`, `taglio_punzonamento`), which all resolve
`fcd = α_cc·fck/γc` with the TOOL's own `inputs.gamma_c`. The two only coincide when the user leaves
`γc` at its 1,5 default (true of every fixture this package's tests use). `output.materiali.
calcestruzzo.fcd_MPa` is therefore never cited by the formulas below: `f_cd` is always rebuilt here
as `α_cc·f_ck/γ_c` with the tool's own `γ_c`, exactly mirroring the formula the traced step actually
evaluated (the same convention `ca_punzonamento.relazione_comune` uses for its own vRd,max)."""
from strutture.shared.relazione import Valore

ALPHA_CC = 0.85  # NTC2018 §4.1.2.1.1.1 / EN 1992-1-1 — coefficiente riduttivo per resistenza di calcolo
# a lungo termine del calcestruzzo; usato (col nome "α_cc") da flessione/puntoni-tiranti/taglio-punzonamento.
FCK_LIMIT_NU_PRIME = 250.0  # EN 1992-1-1 §6.5.2(1)/§6.2.2(1) — ν' = 1-fck/250, ν = 0.6*(1-fck/250).
NU_COEFFICIENT_VRD_MAX = 0.6  # EN 1992-1-1 §6.2.2(6)/§6.4.5(3) — fattore 0,6 di ν per vRd,max.

MM_A_M = 1000.0  # mm -> m (posizioni dei pali, spessori).
KN_A_N = 1000.0  # kN -> N (usato nelle formule espresse in N, poi riscalate).


def valore_gamma_c(gamma_c: float) -> Valore:
    return Valore(simbolo="γ_c", valore=gamma_c, descrizione="coefficiente parziale del calcestruzzo")


def valore_fck(fck_MPa: float) -> Valore:
    return Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica del calcestruzzo")


def valore_fyd(fyd_MPa: float) -> Valore:
    return Valore(simbolo="f_yd", valore=fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio")


def fcd_frammento(fck: str = "f_ck", gamma_c: str = "γ_c") -> str:
    """`α_cc·fck/γc`, α_cc folded as a bare literal (fixed stress-block-style factor, not a
    normative coefficient a reader looks up — same convention as `ca_punzonamento.relazione_comune`)."""
    return f"({ALPHA_CC:g} * {fck} / {gamma_c})"


def nu_prime_frammento(fck: str = "f_ck") -> str:
    """`1 - fck/250` (EN 1992-1-1 §6.5.2(1))."""
    return f"(1 - {fck} / {FCK_LIMIT_NU_PRIME:g})"


def nu_vrd_max_frammento(fck: str = "f_ck") -> str:
    """`0,6*(1 - fck/250)` (EN 1992-1-1 §6.2.2(6)/§6.4.5(3))."""
    return f"({NU_COEFFICIENT_VRD_MAX:g} * (1 - {fck} / {FCK_LIMIT_NU_PRIME:g}))"

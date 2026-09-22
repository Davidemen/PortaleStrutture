"""Verified restatement of `sisma-spettro` (NTC2018 §3.2.3.2.1 eq. 3.2.4-3.2.7, §3.2.3.5;
docs/architecture-phase2.md §6, wave 3 adoption). `SismaSpettroOutput.punti` samples 0-4 s every
0.05 s by default (up to 80+ rows): per docs/architecture-phase2.md §6, a many-rows tool traces
representative points only, never every row — here the FIVE points that exercise every branch of
Se(T)/Sd(T): T=0, T_B, T_C, T_D, and one T>T_D (`T_D + 1` s, always past the last branch boundary
regardless of the actual sampling range). Each is evaluated by calling the package's own
`se_elastico`/`valore_spettro` directly (the calculation code is never touched, not one number);
none of the five needs to land on an actual sampled row of `output.punti` — the branch formulas are
closed-form at any T, and `punti` is a tuple the harness does not cross-check row-by-row
(`tests/shared/relazione/harness.py`: "Tuples of rows are not recursed into").

Se(T)'s 0≤T<T_B branch keeps η inside the reciprocal term (`η·ag·S·F0·[T/TB + 1/(η·F0)·(1-T/TB)]`,
NTC2018 eq. 3.2.4) — the FIXED behaviour this relazione always describes (`legacy_compat=False`,
docs/architecture-phase2.md §1): the sheet's own bug drops η there (`docs/divergences/sisma.md`),
never exercised here. Sd(T) for ULS states substitutes η→1/q into that SAME eq. 3.2.4 rather than
dividing Se(T) by q (NTC2018 §3.2.3.5): algebraically different from Se(T)/q only on the 0≤T<T_B
branch (η also appears inside the reciprocal there), identical to it on every other branch — every
ULS `Sd` `clausola` cites §3.2.3.5 ONLY: the lower bound "Sd(T) non può assumere valori inferiori a
0,2·ag" is itself a §3.2.3.5 provision (spettro di PROGETTO), not §3.2.3.2.1 (spettro ELASTICO,
which contains no such bound) — a wrong attribution the review caught repeated on every printed
row (review finding WRONG_CLAUSE). The bound is part of every ULS `Sd` formula, whether or not it
actually governs at that point (it does, for this package's golden case, only at T>T_D — the `nota`
says so there); it is called "limite inferiore 0,2·ag" here, never "pavimento" (a literal
mistranslation of the English "floor" that means, in Italian technical usage, the floor of a room —
the same review finding flagged the word itself, not just the clause).
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import SismaSpettroInput, SismaSpettroOutput
from .spettro_elastico import se_elastico
from .spettro_progetto import DESIGN_SPECTRUM_FLOOR_RATIO, valore_spettro
from .stato_limite import is_stato_limite_uls

_LIMITE_INFERIORE = f"{DESIGN_SPECTRUM_FLOOR_RATIO:g} * a_g"
_CLAUSOLA_SE = "NTC2018 §3.2.3.2.1 eq. 3.2.4-3.2.7"
_CLAUSOLA_SD = "NTC2018 §3.2.3.5"


def relazione_spettro(inputs: SismaSpettroInput, output: SismaSpettroOutput) -> tuple[Traccia, ...]:
    """10 passi (5 punti rappresentativi × Se, Sd) in una Traccia."""
    is_uls = is_stato_limite_uls(inputs.stato_limite)
    punti = (
        ("T=0", 0.0), ("T=T_B", inputs.tb_s), ("T=T_C", inputs.tc_s),
        ("T=T_D", inputs.td_s), ("T>T_D", inputs.td_s + 1.0),
    )
    passi: tuple[Passo, ...] = ()
    for etichetta, t_s in punti:
        se_g = se_elastico(t_s, inputs.tb_s, inputs.tc_s, inputs.td_s, inputs.ag_g, inputs.s, inputs.f0, inputs.eta, legacy_compat=False)
        passi = (*passi, _passo_se(etichetta, t_s, inputs, se_g), _passo_sd(etichetta, t_s, inputs, se_g, is_uls=is_uls))
    titolo = f"Spettro di risposta — punti rappresentativi (stato limite {inputs.stato_limite})"
    return (Traccia(titolo=titolo, passi=passi),)


def _ramo(t_s: float, inputs: SismaSpettroInput) -> str:
    if t_s < inputs.tb_s:
        return "salita"
    if t_s < inputs.tc_s:
        return "plateau"
    if t_s < inputs.td_s:
        return "decadimento 1/T"
    return "decadimento 1/T²"


def _valori_base(inputs: SismaSpettroInput) -> tuple[Valore, Valore, Valore]:
    return (
        Valore(simbolo="η", valore=inputs.eta, descrizione="correzione per smorzamento"),
        Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
        Valore(simbolo="S", valore=inputs.s, descrizione="coefficiente di amplificazione del suolo"),
    )


def _passo_se(etichetta: str, t_s: float, inputs: SismaSpettroInput, se_g: float) -> Passo:
    ramo = _ramo(t_s, inputs)
    f0 = Valore(simbolo="F_0", valore=inputs.f0, descrizione="fattore di amplificazione massima dello spettro")
    valore_t = Valore(simbolo="T", valore=t_s, unita="s", descrizione=f"periodo del punto, {etichetta}")
    if ramo == "salita":
        formula = "η * a_g * S * F_0 * (T / T_B + 1 / (η * F_0) * (1 - T / T_B))"
        valori = (*_valori_base(inputs), f0, valore_t, Valore(simbolo="T_B", valore=inputs.tb_s, unita="s"))
    elif ramo == "plateau":
        formula = "η * a_g * S * F_0"
        valori = (*_valori_base(inputs), f0)
    elif ramo == "decadimento 1/T":
        formula = "η * a_g * S * F_0 * (T_C / T)"
        valori = (*_valori_base(inputs), f0, valore_t, Valore(simbolo="T_C", valore=inputs.tc_s, unita="s"))
    else:
        formula = "η * a_g * S * F_0 * (T_C * T_D / T^2)"
        valori = (
            *_valori_base(inputs), f0, valore_t,
            Valore(simbolo="T_C", valore=inputs.tc_s, unita="s"), Valore(simbolo="T_D", valore=inputs.td_s, unita="s"),
        )
    return Passo(
        simbolo=f"S_e({etichetta})", formula=formula, valori=valori,
        risultato=se_g, unita="g", clausola=_CLAUSOLA_SE,
        nota=f"Ordinata dello spettro elastico, ramo {ramo}.",
    )


def _passo_sd(etichetta: str, t_s: float, inputs: SismaSpettroInput, se_g: float, *, is_uls: bool) -> Passo:
    sd_g = _sd_reale(t_s, inputs, se_g, is_uls=is_uls)
    if not is_uls:
        return Passo(
            simbolo=f"S_d({etichetta})", formula="S_e",
            valori=(Valore(simbolo="S_e", valore=se_g, unita="g", descrizione="ordinata dello spettro elastico, calcolata sopra"),),
            risultato=sd_g, unita="g", clausola=_CLAUSOLA_SD,
            nota="Stato limite di esercizio: lo spettro di progetto coincide con quello elastico (q=1).",
        )
    if _ramo(t_s, inputs) == "salita":
        formula = f"max(a_g * S * F_0 / q * (T / T_B) + a_g * S * (1 - T / T_B), {_LIMITE_INFERIORE})"
        valori = (
            Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
            Valore(simbolo="S", valore=inputs.s, descrizione="coefficiente di amplificazione del suolo"),
            Valore(simbolo="F_0", valore=inputs.f0), Valore(simbolo="q", valore=inputs.q, descrizione="fattore di struttura"),
            Valore(simbolo="T", valore=t_s, unita="s"), Valore(simbolo="T_B", valore=inputs.tb_s, unita="s"),
        )
    else:
        # NTC2018 §3.2.3.5: η REPLACED by 1/q — S_e carries η, so S_e/(η·q) = a_g·S·F_0·(…)/q
        formula = f"max(S_e / (η * q), {_LIMITE_INFERIORE})"
        valori = (
            Valore(simbolo="S_e", valore=se_g, unita="g", descrizione="ordinata dello spettro elastico, calcolata sopra (contiene η)"),
            Valore(simbolo="η", valore=inputs.eta, descrizione="correzione per smorzamento, sostituita da 1/q nello spettro di progetto"),
            Valore(simbolo="q", valore=inputs.q, descrizione="fattore di struttura"),
            Valore(simbolo="a_g", valore=inputs.ag_g, unita="g"),
        )
    raw_senza_limite = _sd_uls_senza_limite_inferiore(t_s, inputs, se_g)
    limite_inferiore_vale = DESIGN_SPECTRUM_FLOOR_RATIO * inputs.ag_g
    nota = "Spettro di progetto (stato limite ultimo): riduzione per q, con il limite inferiore 0,2·ag."
    if limite_inferiore_vale > raw_senza_limite:
        nota += " In questo punto il limite inferiore governa (il termine ridotto per q sarebbe inferiore)."
    return Passo(simbolo=f"S_d({etichetta})", formula=formula, valori=valori, risultato=sd_g, unita="g", clausola=_CLAUSOLA_SD, nota=nota)


def _sd_uls_senza_limite_inferiore(t_s: float, inputs: SismaSpettroInput, se_g: float) -> float:
    """Same arithmetic as `spettro_progetto._sd_uls`, restated for the `nota`'s "does the lower
    bound govern here" comparison — NOT used as any Passo's `risultato` (the bound always applies
    to that, matching `valore_spettro`)."""
    if t_s < inputs.tb_s:
        return inputs.ag_g * inputs.s * inputs.f0 / inputs.q * (t_s / inputs.tb_s) + inputs.ag_g * inputs.s * (1.0 - t_s / inputs.tb_s)
    return se_g / inputs.eta / inputs.q


def _sd_reale(t_s: float, inputs: SismaSpettroInput, se_g: float, *, is_uls: bool) -> float:
    return valore_spettro(
        se_g, inputs.q, t_s, is_uls=is_uls, ag_g=inputs.ag_g, s=inputs.s, f0=inputs.f0, tb_s=inputs.tb_s, eta=inputs.eta, legacy_compat=False,
    )

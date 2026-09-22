"""Verified restatement of `ca-sle-limitazione-tensioni` (docs/architecture-phase2.md §6, wave
2/3 adoption) — NTC2018 §4.1.2.2.5, sheet `Limitazione delle tensioni`. `f_ck` is derived once
(`limitazione_tensioni.fck_da_rck`) and then reused, as a `Valore` citing "calcolata sopra", by
every one of the three repeated sections; each section restates its own Check exactly as
`tool.py::_checks_sezione_tensioni` builds it (`Check.passed` comes straight from
`verifica.verificato`, a STRICT `limite > agente`, so every comparison here uses `<` to match —
see the module's own worked note for why an exact boundary equality would otherwise disagree with
`Report.checks`).

`utilizzo_c_rar` (`σ_c,rara/σ_c,rara,lim`) is the one highlighted ratio of the three per-section
outputs (`models.py`'s own comment: only the concrete/rara column is flagged, the sheet's own
choice) — restated as an informative `Passo` right after its Check, per docs/architecture-phase2.md
§6 lesson 4 ("an informative ratio that is NOT a normative check must say so in its title").

13 passi (1 + 3×4) across 4 `Traccia`, covering all 9 `Check` this tool emits and its highlighted
output."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .limitazione_tensioni import COEFF_SIGMA_C_MAX_QPE, COEFF_SIGMA_C_MAX_RAR, COEFF_SIGMA_S_MAX_RAR, RAPPORTO_FCK_RCK
from .models import LimitazioneTensioniInput, LimitazioneTensioniOutput, VerificaTensioneSezione
from .sezioni import SEZIONI

CLAUSOLA = "NTC2018 §4.1.2.2.5"


def relazione_limitazione_tensioni(
    inputs: LimitazioneTensioniInput, output: LimitazioneTensioniOutput
) -> tuple[Traccia, ...]:
    valori_sezioni = (
        (inputs.sigma_c_rar_1_MPa, inputs.sigma_c_qpe_1_MPa, inputs.sigma_s_rar_1_MPa),
        (inputs.sigma_c_rar_2_MPa, inputs.sigma_c_qpe_2_MPa, inputs.sigma_s_rar_2_MPa),
        (inputs.sigma_c_rar_3_MPa, inputs.sigma_c_qpe_3_MPa, inputs.sigma_s_rar_3_MPa),
    )
    tracce = [_traccia_fck(inputs, output)]
    for indice, ((titolo, sottotitolo), agenti, sezione) in enumerate(zip(SEZIONI, valori_sezioni, output.sezioni, strict=True)):
        tracce.append(_traccia_sezione(indice, titolo, sottotitolo, agenti, sezione, output.fck_MPa, inputs.fyk_MPa))
    return tuple(tracce)


def _traccia_fck(inputs: LimitazioneTensioniInput, output: LimitazioneTensioniOutput) -> Traccia:
    return Traccia(
        titolo="Materiali",
        passi=(
            Passo(
                simbolo="f_ck",
                formula=f"{RAPPORTO_FCK_RCK:g} * R_ck",
                valori=(Valore(simbolo="R_ck", valore=inputs.rck_MPa, unita="MPa", descrizione="resistenza cubica caratteristica del calcestruzzo"),),
                risultato=output.fck_MPa, unita="MPa", clausola="NTC2018 §11.2.10.1",
                nota="Conversione da resistenza cubica a resistenza cilindrica caratteristica.",
            ),
        ),
    )


def _titolo_sezione(indice: int, titolo: str, sottotitolo: str) -> str:
    suffisso = f", {sottotitolo.lower()}" if sottotitolo else ""
    return f"Sezione {indice + 1} — {titolo}{suffisso}"


def _traccia_sezione(
    indice: int, titolo: str, sottotitolo: str, agenti: tuple[float, float, float],
    sezione: VerificaTensioneSezione, fck_MPa: float, fyk_MPa: float,
) -> Traccia:
    sigma_c_rar, sigma_c_qpe, sigma_s_rar = agenti
    return Traccia(
        titolo=_titolo_sezione(indice, titolo, sottotitolo),
        passi=(
            _passo_sigma_c(sigma_c_rar, fck_MPa, COEFF_SIGMA_C_MAX_RAR, "σ_c,rara", "rara", sezione.verificato_c_rar),
            _passo_utilizzo_c_rara(sigma_c_rar, sezione.sigma_c_max_rar_MPa, sezione.utilizzo_c_rar),
            _passo_sigma_c(sigma_c_qpe, fck_MPa, COEFF_SIGMA_C_MAX_QPE, "σ_c,qp", "quasi permanente", sezione.verificato_c_qpe),
            _passo_sigma_s(sigma_s_rar, fyk_MPa, sezione.verificato_s_rar),
        ),
    )


def _passo_sigma_c(agente_MPa: float, fck_MPa: float, coeff: float, simbolo: str, combinazione: str, verificata: bool) -> Passo:
    return Passo(
        simbolo=simbolo,
        formula=f"{simbolo} < {coeff:g} * f_ck",
        valori=(
            Valore(simbolo=simbolo, valore=agente_MPa, unita="MPa", descrizione=f"tensione nel calcestruzzo, combinazione {combinazione}"),
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),
        ),
        risultato=agente_MPa, unita="MPa", clausola=CLAUSOLA,
        esito="soddisfatta" if verificata else "non soddisfatta",
        nota=f"Limite {coeff:g}·f_ck, combinazione {combinazione}.",
    )


def _passo_utilizzo_c_rara(agente_MPa: float, limite_MPa: float, utilizzo: float) -> Passo:
    return Passo(
        simbolo="σ_c,rara/σ_c,rara,lim", formula="σ_c,rara / σ_c,rara,lim",
        valori=(
            Valore(simbolo="σ_c,rara", valore=agente_MPa, unita="MPa", descrizione="tensione agente, calcolata sopra"),
            Valore(simbolo="σ_c,rara,lim", valore=limite_MPa, unita="MPa", descrizione="tensione limite, calcolata sopra"),
        ),
        risultato=utilizzo, unita="-",
        nota="Tasso di sfruttamento informativo (non un Check separato: la verifica è il confronto sopra).",
    )


def _passo_sigma_s(agente_MPa: float, fyk_MPa: float, verificata: bool) -> Passo:
    return Passo(
        simbolo="σ_s,rara",
        formula=f"σ_s,rara < {COEFF_SIGMA_S_MAX_RAR:g} * f_yk",
        valori=(
            Valore(simbolo="σ_s,rara", valore=agente_MPa, unita="MPa", descrizione="tensione nell'acciaio, combinazione rara"),
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio"),
        ),
        risultato=agente_MPa, unita="MPa", clausola=CLAUSOLA,
        esito="soddisfatta" if verificata else "non soddisfatta",
        nota=f"Limite {COEFF_SIGMA_S_MAX_RAR:g}·f_yk, combinazione rara.",
    )

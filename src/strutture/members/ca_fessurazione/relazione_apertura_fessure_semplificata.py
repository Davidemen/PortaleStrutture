"""Verified restatement of `ca-apertura-fessure-semplificata` (docs/architecture-phase2.md §6,
wave 2/3 adoption) — NTC2018 §4.1.2.2.4, sheet `Apertura delle fessure SEMP`: the simplified
table method (no crack-width formula, a bare steel-stress limit read off Tab. C4.1.II by bar
diameter and crack-width class). `classe_fre`/`classe_qpe` (Tab. 4.1.IV, by exposure/combination/
sensitivity) are resolved ONCE — `tool.py::_classi_apertura_semplificata` calls it identically for
the three sections, since neither input varies per section — and then reused, as a `Valore`
citing "calcolata sopra", by every section's two stress limits.

Both `σ_s,fre,lim`/`σ_s,qp,lim` are pure Tab. C4.1.II lookups (`rebar_catalog.sigma_limit_by_
diameter`, interpolated by bar diameter): no formula an engineer would write, so each gets the
short lookup `Passo` docs/architecture-phase2.md §6 calls for — `formula` is the identifier
itself, `nota` names the table. Every comparison uses STRICT `<` to match `verifica.verificato`
(`limite > agente`, see `relazione_limitazione_tensioni.py`'s module docstring). `utilizzo_fre`
(`σ_s,fre/σ_s,fre,lim`) is the one highlighted ratio per section (the sheet's own choice, same
asymmetry as tool 1's `utilizzo_c_rar`): restated as an informative `Passo` right after its Check.

17 passi (2 + 3×5) across 4 `Traccia`, covering all 6 `Check` this tool emits and its highlighted
output."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .classe_apertura_normativa import classe_normativa_fre, classe_normativa_qpe
from .models import AperturaFessureSempInput, AperturaFessureSempOutput, VerificaSemplificataSezione
from .sezioni import SEZIONI

CLAUSOLA = "NTC2018 §4.1.2.2.4"
_WK_MM_PER_CLASSE = {"w1": 0.2, "w2": 0.3, "w3": 0.4}  # NTC2018 Tab. 4.1.IV, per la nota del lookup.


def relazione_apertura_fessure_semplificata(
    inputs: AperturaFessureSempInput, output: AperturaFessureSempOutput
) -> tuple[Traccia, ...]:
    prima_sezione = output.sezioni[0]
    tracce = [_traccia_classe(inputs, prima_sezione)]
    diametri_agenti = (
        (inputs.diametro_mm_1, inputs.sigma_fre_MPa_1, inputs.sigma_qpe_MPa_1),
        (inputs.diametro_mm_2, inputs.sigma_fre_MPa_2, inputs.sigma_qpe_MPa_2),
        (inputs.diametro_mm_3, inputs.sigma_fre_MPa_3, inputs.sigma_qpe_MPa_3),
    )
    for indice, ((titolo, sottotitolo), _, sezione) in enumerate(zip(SEZIONI, diametri_agenti, output.sezioni, strict=True)):
        tracce.append(_traccia_sezione(indice, titolo, sottotitolo, sezione))
    return tuple(tracce)


def _traccia_classe(inputs: AperturaFessureSempInput, sezione: VerificaSemplificataSezione) -> Traccia:
    classe_fre, classe_qpe = sezione.classe_fre, sezione.classe_qpe
    nota = (
        f"Classe applicata per condizioni ambientali '{inputs.condizioni_ambientali}' e sensibilità "
        f"dell'armatura '{inputs.sensibilita_armatura}', identica per le tre sezioni; riverificata da "
        f"classe_normativa_fre/qpe = {classe_normativa_fre(inputs.condizioni_ambientali, inputs.sensibilita_armatura)}/"
        f"{classe_normativa_qpe(inputs.condizioni_ambientali, inputs.sensibilita_armatura)}."
    )
    return Traccia(
        titolo="Classe di apertura fessura applicata",
        passi=(
            _passo_classe("classe_fre", classe_fre, "combinazione frequente", nota),
            _passo_classe("classe_qpe", classe_qpe, "combinazione quasi permanente", nota),
        ),
    )


def _passo_classe(simbolo: str, classe: str, combinazione: str, nota: str) -> Passo:
    """Review finding (MISLEADING, mirroring `ca_travi/relazione_sle.py::_passo_classe_conforme`):
    a generic `formula=simbolo` (e.g. "classe_fre = classe_fre") would print the w_k limit without
    ever showing WHICH class (w1/w2/w3) it belongs to. The class label itself is the identifier."""
    return Passo(
        simbolo=simbolo, formula=classe,
        valori=(Valore(simbolo=classe, valore=_WK_MM_PER_CLASSE[classe], unita="mm", descrizione=f"limite w_k della classe {classe}"),),
        risultato=_WK_MM_PER_CLASSE[classe], unita="mm",
        nota=f"Classe {classe} ({combinazione}), NTC2018 Tab. 4.1.IV. {nota}",
    )


def _titolo_sezione(indice: int, titolo: str, sottotitolo: str) -> str:
    suffisso = f", {sottotitolo.lower()}" if sottotitolo else ""
    return f"Sezione {indice + 1} — {titolo}{suffisso}"


def _traccia_sezione(indice: int, titolo: str, sottotitolo: str, sezione: VerificaSemplificataSezione) -> Traccia:
    return Traccia(
        titolo=_titolo_sezione(indice, titolo, sottotitolo),
        passi=(
            _passo_limite("σ_s,fre,lim", sezione.diametro_mm, sezione.sigma_lim_fre_MPa, sezione.classe_fre),
            _passo_check("σ_s,fre", sezione.sigma_fre_MPa, "σ_s,fre,lim", sezione.sigma_lim_fre_MPa, "frequente", sezione.verificato_fre),
            _passo_utilizzo_fre(sezione.sigma_fre_MPa, sezione.sigma_lim_fre_MPa, sezione.utilizzo_fre),
            _passo_limite("σ_s,qp,lim", sezione.diametro_mm, sezione.sigma_lim_qpe_MPa, sezione.classe_qpe),
            _passo_check("σ_s,qp", sezione.sigma_qpe_MPa, "σ_s,qp,lim", sezione.sigma_lim_qpe_MPa, "quasi permanente", sezione.verificato_qpe),
        ),
    )


def _passo_utilizzo_fre(agente_MPa: float, limite_MPa: float, utilizzo: float) -> Passo:
    return Passo(
        simbolo="σ_s,fre/σ_s,fre,lim", formula="σ_s,fre / σ_s,fre,lim",
        valori=(
            Valore(simbolo="σ_s,fre", valore=agente_MPa, unita="MPa", descrizione="tensione agente, combinazione frequente"),
            Valore(simbolo="σ_s,fre,lim", valore=limite_MPa, unita="MPa", descrizione="limite tabellare, calcolato sopra"),
        ),
        risultato=utilizzo, unita="-",
        nota="Tasso di sfruttamento informativo (non un Check separato: la verifica è il confronto sopra).",
    )


def _passo_limite(simbolo: str, diametro_mm: float, limite_MPa: float, classe: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=limite_MPa, unita="MPa", descrizione=f"limite tabellare per ⌀={diametro_mm:g} mm, classe {classe}"),),
        risultato=limite_MPa, unita="MPa",
        nota=f"Lettura di Tab. C4.1.II (Circolare 7/2019) per il diametro ⌀={diametro_mm:g} mm e la classe {classe}, interpolata fra i diametri tabellati.",
    )


def _passo_check(simbolo_agente: str, agente_MPa: float, simbolo_limite: str, limite_MPa: float, combinazione: str, verificata: bool) -> Passo:
    return Passo(
        simbolo=simbolo_agente,
        formula=f"{simbolo_agente} < {simbolo_limite}",
        valori=(
            Valore(simbolo=simbolo_agente, valore=agente_MPa, unita="MPa", descrizione=f"tensione nell'acciaio, combinazione {combinazione}"),
            Valore(simbolo=simbolo_limite, valore=limite_MPa, unita="MPa", descrizione="limite tabellare, calcolato sopra"),
        ),
        risultato=agente_MPa, unita="MPa", clausola=CLAUSOLA,
        esito="soddisfatta" if verificata else "non soddisfatta",
        nota=f"Verifica indiretta dell'apertura di fessura per confronto tabellare, combinazione {combinazione}.",
    )

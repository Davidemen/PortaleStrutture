"""Verified restatement (docs/architecture-phase2.md) of `interazione.py` (N-My-Mz interaction,
EN1993-1-1 §6.3.3 eq. 6.61/6.62 — column-check!Y47/Y50).

C_my/C_mz/C_mLT (`annex_a_cm.py`) are a 4-branch table lookup keyed on the moment-diagram type
(EN1993-1-1 Annex B Tab. B.3, referenced by the Annex A method) — restated here as a `Passo` whose
`formula` is the identifier itself (docs/architecture-phase2.md §6's "lookup only" fallback),
mirroring `ca_travi.relazione_sle`'s σ_s,limite treatment, with the active table branch named in the
`nota`. k_yy/k_yz/k_zy/k_zz (`annex_a_kij.py`) are EN1993-1-1 Annex A Tab. A.1: each is the most
elaborate quantity in the whole verification (`annex_a_kij.py`'s own Cyy/Cyz/Czy/Czz chains, in
turn, depend on μ, N_cr, λ̄_max and the class), far beyond the notation grammar's arithmetic
whitelist to restate in closed form — each now gets the SAME "lookup only" `Passo` the simpler
C_my/C_mz/C_mLT already had (review finding MISSING_STEP: they used to be bare inline `Valore`s
with no `Passo` of their own, unlike every table-value lookup in the loads packages), cited from
`ColonnaEc3Output.interazione`, never re-derived.

Fixed mode (§6.3.3 eq. 6.61/6.62, non-legacy branch of `interazione.py`): BOTH utilisation formulas
divide the CHARACTERISTIC resistances (N_Rk=A·f_yk, M_i,Rk=W_i·f_yk) by γ_M1 with the SAME grouping
— the legacy sheet's eq. 6.61 has an extra γ_M1 in its third term (a documented, unfixed-here
divergence in `interazione.py`'s own docstring) and uses the DESIGN (fyd-based) resistances instead;
`relazione` only ever describes standard mode.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from . import annex_a_cm as cm
from .models import ColonnaEc3Input
from .results import ColonnaEc3Output

_TABELLA_CM = "EN1993-1-1 Annex A (metodo) / Annex B Tab. B.3 (C_m)"
_TABELLA_KIJ = "EN1993-1-1 Annex A Tab. A.1"


def traccia_interazione(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """9 passi: C_my, C_mz, C_mLT, k_yy, k_yz, k_zy, k_zz, utilizzo (yy) [Check], utilizzo (zz) [Check]."""
    return Traccia(
        titolo="Interazione N-My-Mz (metodo Annex A)",
        passi=(
            _passo_cm(inputs, output, "y"), _passo_cm(inputs, output, "z"), _passo_cm_lt(inputs, output),
            _passo_kij(output, "k_yy"), _passo_kij(output, "k_yz"), _passo_kij(output, "k_zy"), _passo_kij(output, "k_zz"),
            _passo_utilizzo(inputs, output, "yy"), _passo_utilizzo(inputs, output, "zz"),
        ),
    )


def _passo_kij(output: ColonnaEc3Output, simbolo: str) -> Passo:
    valore = getattr(output.interazione, simbolo.replace("k_", "k"))  # kyy/kyz/kzy/kzz
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione=f"fattore di interazione, {_TABELLA_KIJ}"),),
        risultato=valore, unita="-", clausola=_TABELLA_KIJ,
        nota="Dipende da classe, C_m, μ=(1−N_sd/N_cr)/(1−χ·N_sd/N_cr), n=N_sd/N_Rk e dai fattori "
             "C_yy/C_yz/C_zy/C_zz di Tab. A.1 (annex_a_kij.py): non restatabile in forma chiusa "
             "nella grammatica delle notazioni (docs/architecture-phase2.md §2), citato per identità "
             "come le altre grandezze tabellari di questo pacchetto.",
    )


def _correzione_torsionale_attiva(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> bool:
    soglia = cm.soglia_lambda0(
        inputs.c1, inputs.nsd_kN, output.instabilita_flessionale.ncr_z_kN, output.instabilita_flessionale.ncr_t_kN,
    )
    return output.instabilita_torso_flessionale.lambda_lt > soglia


def _passo_cm(inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str) -> Passo:
    tipo = inputs.diagramma_tipo_y if asse == "y" else inputs.diagramma_tipo_z
    simbolo = f"C_m{asse}"
    valore = output.interazione.cmy if asse == "y" else output.interazione.cmz
    nota = f'Diagramma dei momenti tipo "{tipo}" (Tab. B.3).'
    if asse == "y":
        nota += (
            f" Correzione torsionale {'applicata' if _correzione_torsionale_attiva(inputs, output) else 'non applicata'} "
            "(attiva quando λ_LT supera la soglia dell'Annex A)."
        )
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione=f"fattore di momento uniforme equivalente, {_TABELLA_CM}"),),
        risultato=valore, unita="-", clausola=_TABELLA_CM, nota=nota,
    )


def _passo_cm_lt(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    correzione = _correzione_torsionale_attiva(inputs, output)
    valore = output.interazione.cm_lt
    return Passo(
        simbolo="C_mLT", formula="C_mLT",
        valori=(Valore(simbolo="C_mLT", valore=valore, descrizione=f"fattore di momento uniforme equivalente per l'instabilità flesso-torsionale, {_TABELLA_CM}"),),
        risultato=valore, unita="-", clausola=_TABELLA_CM,
        nota="Vale 1 quando λ_LT non supera la soglia dell'Annex A." if not correzione else "",
    )


def _passo_utilizzo(inputs: ColonnaEc3Input, output: ColonnaEc3Output, piano: str) -> Passo:
    """`piano`: "yy" (eq. 6.61) o "zz" (eq. 6.62)."""
    interaz, sezione, materiali = output.interazione, output.sezione, output.materiali
    if piano == "yy":
        chi_simbolo, chi_valore = "χ_yy", output.instabilita_flessionale.chi_yy
        k_diretto_simbolo, k_diretto_valore = "k_yy", interaz.kyy
        k_incrociato_simbolo, k_incrociato_valore = "k_yz", interaz.kyz
        risultato, passed = interaz.utilizzo_yy, interaz.verifica_yy.passed
        clausola = "EN1993-1-1 §6.3.3 eq. (6.61)"
    else:
        chi_simbolo, chi_valore = "χ_zz", output.instabilita_flessionale.chi_zz
        k_diretto_simbolo, k_diretto_valore = "k_zy", interaz.kzy
        k_incrociato_simbolo, k_incrociato_valore = "k_zz", interaz.kzz
        risultato, passed = interaz.utilizzo_zz, interaz.verifica_zz.passed
        clausola = "EN1993-1-1 §6.3.3 eq. (6.62)"
    return Passo(
        simbolo=f"N_Ed/N_Rd + ΣM_Ed/M_Rd ({piano})",
        formula=(
            f"N_sd/({chi_simbolo}*N_Rk/γ_M1) + {k_diretto_simbolo}*M_y,sd/(χ_LT*M_y,Rk/γ_M1) "
            f"+ {k_incrociato_simbolo}*M_z,sd/(M_z,Rk/γ_M1) < 1"
        ),
        valori=(
            Valore(simbolo="N_sd", valore=inputs.nsd_kN, unita="kN"),
            Valore(simbolo=chi_simbolo, valore=chi_valore, descrizione="calcolato sopra"),
            Valore(simbolo="N_Rk", valore=sezione.npl_rk_kN, unita="kN", descrizione="resistenza plastica assiale CARATTERISTICA, N_Rk=A·f_yk"),
            Valore(simbolo="γ_M1", valore=materiali.gamma_m1, descrizione="fattore parziale di sicurezza per la resistenza all'instabilità"),
            Valore(simbolo=k_diretto_simbolo, valore=k_diretto_valore, descrizione="calcolato sopra"),
            Valore(simbolo="M_y,sd", valore=inputs.my_sd_kNm, unita="kNm"),
            Valore(simbolo="χ_LT", valore=output.instabilita_torso_flessionale.chi_lt, descrizione="calcolato sopra"),
            Valore(simbolo="M_y,Rk", valore=sezione.mpl_y_rk_kNm, unita="kNm", descrizione="momento resistente CARATTERISTICO, W·f_yk"),
            Valore(simbolo=k_incrociato_simbolo, valore=k_incrociato_valore, descrizione="calcolato sopra"),
            Valore(simbolo="M_z,sd", valore=inputs.mz_sd_kNm, unita="kNm"),
            Valore(simbolo="M_z,Rk", valore=sezione.mpl_z_rk_kNm, unita="kNm", descrizione="momento resistente CARATTERISTICO, W·f_yk"),
        ),
        risultato=risultato, unita="-", clausola=clausola,
        esito="soddisfatta" if passed else "non soddisfatta",
    )

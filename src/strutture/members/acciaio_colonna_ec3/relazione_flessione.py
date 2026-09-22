"""Verified restatement (docs/architecture-phase2.md) of `flessione.py` (M_Rd,y / M_Rd,z, with the
high-shear reduction of EN1993-1-1 §6.2.8 — column-check!D33/D43). Standard-mode pairing only
(`flessione.costruisci_flessione`'s non-legacy branch): the reduction trigger and the reduction
factor share the SAME demand (`vy_sd_kN` for M_Rd,y/web, `vz_sd_kN` for M_Rd,z/flange, matching the
web/flange pairing of `relazione_taglio.py`) — the legacy sheet swaps trigger vs. reduction axis, a
documented, unfixed-here divergence in `flessione.py`'s own docstring. Printed as `V_Ed,w`/`V_Ed,f`,
not `V_y,sd`/`V_z,sd`, for the same reason `relazione_taglio.py` does (its own docstring): the
calculation code's own field names (`vy_sd_kN` for the WEB demand) are the reverse of EN1993-1-1's
axis convention, a naming issue this relazione module cannot fix in `models.py`/`flessione.py`
(review finding MISLEADING).

The reduction only gets its own `Passo` (f_yd -> f_y') when it actually applies (§6.2.8(3),
V_Ed ≥ 0,5·V_pl,Rd): most real designs have low shear, so the common case stays a single `Passo`
per axis, mirroring `ca_travi.relazione_sle`'s optional-block sizing philosophy. `f_y'` is cited
from `V_pl,Rd,w`/`V_pl,Rd,f` of `relazione_taglio.py`, never re-derived.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .flessione import fy_ridotta_MPa
from .models import ColonnaEc3Input
from .relazione_comune import NMM_A_KNM, modulo_flessionale
from .results import ColonnaEc3Output
from .sezione import numero_classe

_ASSE_DEMANDA = {"y": ("V_Ed,w", "V_pl,Rd,w"), "z": ("V_Ed,f", "V_pl,Rd,f")}


def traccia_flessione(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """2 (nessuna riduzione) o 4 (riduzione su uno o entrambi gli assi) passi."""
    passi: tuple[Passo, ...] = ()
    for asse in ("y", "z"):
        passi = (*passi, *_passi_asse(inputs, output, asse))
    return Traccia(titolo="Resistenza a flessione, con riduzione per taglio elevato", passi=passi)


def _passi_asse(inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str) -> tuple[Passo, ...]:
    simbolo_v, simbolo_vpl = _ASSE_DEMANDA[asse]
    v_sd = inputs.vy_sd_kN if asse == "y" else inputs.vz_sd_kN
    vpl_rd = output.taglio.vpl_rd_anima_kN if asse == "y" else output.taglio.vpl_rd_ali_kN
    riduzione_attiva = not (v_sd < 0.5 * vpl_rd)
    fy_simbolo = "f_yd" if not riduzione_attiva else f"f'_{asse}"
    fy_valore = output.materiali.fyd_MPa if not riduzione_attiva else (
        output.flessione.fy_ridotta_y_MPa if asse == "y" else output.flessione.fy_ridotta_z_MPa
    )
    passi = ()
    if riduzione_attiva:
        passi = (_passo_fy_ridotta(inputs, output, asse, simbolo_v, simbolo_vpl, v_sd, vpl_rd),)
    return (*passi, _passo_mrd(inputs, output, asse, fy_simbolo, fy_valore, riduzione_attiva))


def _passo_fy_ridotta(
    inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str,
    simbolo_v: str, simbolo_vpl: str, v_sd: float, vpl_rd: float,
) -> Passo:
    fy_valore = fy_ridotta_MPa(v_sd, v_sd, vpl_rd, output.materiali.fyd_MPa)
    return Passo(
        simbolo=f"f_y' ({asse})",
        formula=f"(1 - (2*{simbolo_v}/{simbolo_vpl} - 1)^2) * f_yd",
        valori=(
            Valore(simbolo=simbolo_v, valore=v_sd, unita="kN"),
            Valore(simbolo=simbolo_vpl, valore=vpl_rd, unita="kN", descrizione="calcolato sopra"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa", descrizione="calcolato sopra"),
        ),
        risultato=fy_valore, unita="MPa", clausola="EN1993-1-1 §6.2.8(3) eq. (6.29)",
        nota=f"{simbolo_v} ≥ 0,5·{simbolo_vpl}: taglio elevato, riduzione della tensione di snervamento di progetto.",
    )


def _passo_mrd(
    inputs: ColonnaEc3Input, output: ColonnaEc3Output, asse: str,
    fy_simbolo: str, fy_valore: float, riduzione_attiva: bool,
) -> Passo:
    classe_num = numero_classe(inputs.classe_sezione)
    wel = inputs.wel_y_mm3 if asse == "y" else inputs.wel_z_mm3
    wpl = inputs.wpl_y_mm3 if asse == "y" else inputs.wpl_z_mm3
    simbolo_modulo, modulo = modulo_flessionale(classe_num, wel, wpl, asse)
    m_sd_simbolo = f"M_{asse},sd"
    m_sd = inputs.my_sd_kNm if asse == "y" else inputs.mz_sd_kNm
    risultato = output.flessione.mrd_y_kNm if asse == "y" else output.flessione.mrd_z_kNm
    passed = output.flessione.verifica_y.passed if asse == "y" else output.flessione.verifica_z.passed
    simbolo_v, simbolo_vpl = _ASSE_DEMANDA[asse]
    v_sd = inputs.vy_sd_kN if asse == "y" else inputs.vz_sd_kN
    vpl_rd = output.taglio.vpl_rd_anima_kN if asse == "y" else output.taglio.vpl_rd_ali_kN
    nota = (
        "" if riduzione_attiva else
        f"{simbolo_v}={v_sd:g} kN < 0,5·{simbolo_vpl}={0.5*vpl_rd:g} kN: nessuna riduzione per taglio "
        "elevato, §6.2.8(2)."
    )
    return Passo(
        simbolo=f"M_Rd,{asse}",
        formula=f"{simbolo_modulo} * {fy_simbolo} * {NMM_A_KNM:g} >= {m_sd_simbolo}",
        valori=(
            Valore(simbolo=simbolo_modulo, valore=modulo, unita="mm3", descrizione=f"modulo di resistenza (classe {classe_num})"),
            Valore(simbolo=fy_simbolo, valore=fy_valore, unita="MPa", descrizione="calcolato sopra" if riduzione_attiva else "tensione di calcolo di snervamento (nessuna riduzione)"),
            Valore(simbolo=m_sd_simbolo, valore=m_sd, unita="kNm"),
        ),
        risultato=risultato, unita="kNm", clausola="EN1993-1-1 §6.2.5" + ("/§6.2.8" if riduzione_attiva else ""),
        esito="soddisfatta" if passed else "non soddisfatta", nota=nota,
    )

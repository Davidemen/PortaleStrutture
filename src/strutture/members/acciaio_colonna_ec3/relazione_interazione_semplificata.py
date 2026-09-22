"""Verified restatement (docs/architecture-phase2.md) of `interazione_semplificata.py` (simplified
fallback interaction checks, EN1993-1-1 §6.2.9.1 — column-check!H46-H52, J53/J54, V54, I56). Fixed
mode only (`costruisci_interazione_semplificata`'s non-legacy branch): `a` (the flange area ratio,
eq. 6.38a) is the SAME value for both axes and M_N,z,Rd follows §6.2.9.1(5)'s own branching z-axis
formula (`mn_rd_z_kNm_fixed`) — the legacy sheet reuses a web-based `a_zz` and the y-axis
interpolation formula for z too, a documented, unfixed-here divergence in
`interazione_semplificata.py`'s own docstring.

§6.2.9.1 is titled "Class 1 and 2 cross-sections" (class 3 is §6.2.9.2, the elastic σ≤fy/γM0
criterion): this whole block is applied regardless of the section's declared class, as a simplified
CROSS-CHECK against the Annex A interaction of `relazione_interazione.py` — the Traccia title says
so (review finding WRONG_CLAUSE). I56's power interaction is eq. (6.41) of §6.2.9.1(6), not §6.2.1(7)
(`interazione_semplificata.py`'s own docstring already says so; the previous `Check(clause=...)` the
trace used to copy cited §6.2.1(7), review finding WRONG_CLAUSE). `M_pl,{y,z},Rd`/`M_c,{y,z},Rd`
(`relazione_comune.simbolo_momento_rd`) matches whichever symbol `relazione_sezione.py` printed for
the same quantity (plastic for class 1-2, elastic for class 3-4): the outcome stays conservative
because `sezione.py` already feeds `W_el` for class ≥3 (`modulo_flessionale`), but the LABEL must
say so too.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .relazione_comune import simbolo_momento_rd
from .results import ColonnaEc3Output
from .sezione import numero_classe


def traccia_interazione_semplificata(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """5 passi: n (riutilizzato), M_N,Rd,y [Check], M_N,Rd,z [Check], V54 [Check], I56 [Check]."""
    return Traccia(
        titolo=(
            "Verifiche semplificate di riscontro (criterio §6.2.9.1, sezioni classe 1-2 — qui "
            "usato come controllo indicativo indipendentemente dalla classe dichiarata)"
        ),
        passi=(
            _passo_n(inputs, output), _passo_mn_rd_y(inputs, output), _passo_mn_rd_z(inputs, output),
            _passo_v54(inputs, output), _passo_i56(inputs, output),
        ),
    )


def _passo_n(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    interaz_semp = output.interazione_semplificata
    return Passo(
        simbolo="n", formula="N_sd / N_pl,Rd",
        valori=(
            Valore(simbolo="N_sd", valore=inputs.nsd_kN, unita="kN"),
            Valore(simbolo="N_pl,Rd", valore=output.sezione.npl_kN, unita="kN", descrizione="calcolato sopra"),
        ),
        risultato=interaz_semp.n_ratio, unita="-", clausola="EN1993-1-1 §6.2.9.1(4)",
        nota="Rapporto di sfruttamento assiale sulla sezione lorda, riutilizzato dalle verifiche seguenti.",
    )


def _passo_mn_rd_y(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    interaz_semp = output.interazione_semplificata
    m_simbolo = simbolo_momento_rd(numero_classe(inputs.classe_sezione), "y")
    return Passo(
        simbolo="M_N,Rd,y",
        formula=f"min({m_simbolo} * (1 - n) / (1 - 0.5*min((A - 2*b*t_f)/A, 0.5)), {m_simbolo}) >= M_y,sd",
        valori=(
            Valore(simbolo=m_simbolo, valore=output.sezione.mpl_y_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="n", valore=interaz_semp.n_ratio, descrizione="calcolato sopra"),
            Valore(simbolo="A", valore=inputs.area_mm2, unita="mm2"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="t_f", valore=inputs.tf_mm, unita="mm"),
            Valore(simbolo="M_y,sd", valore=inputs.my_sd_kNm, unita="kNm"),
        ),
        risultato=interaz_semp.mn_rd_y_kNm, unita="kNm", clausola="EN1993-1-1 §6.2.9.1(5) eq. (6.36)",
        esito="soddisfatta" if interaz_semp.verifica_yy.passed else "non soddisfatta",
        nota="a=min[(A-2·b·t_f)/A; 0,5] è il rapporto d'area delle ali, eq. (6.38a); impiegato per "
             "entrambi gli assi in modalità standard.",
    )


def _passo_mn_rd_z(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    interaz_semp = output.interazione_semplificata
    m_simbolo = simbolo_momento_rd(numero_classe(inputs.classe_sezione), "z")
    n, a = interaz_semp.n_ratio, min((inputs.area_mm2 - 2.0 * inputs.b_mm * inputs.tf_mm) / inputs.area_mm2, 0.5)
    # Il ramo (eq. 6.39a vs 6.39b) va nel simbolo stampato, non solo nella nota (`traccia_a_testo`
    # non stampa mai `Passo.nota`, review finding MISSING_STEP): altrimenti "M_N,Rd,z = M_pl,z,Rd"
    # si legge come una legge incondizionata, non come l'esito del solo ramo n ≤ a.
    if n <= a:
        simbolo = "M_N,Rd,z  (n ≤ a)"
        formula = f"{m_simbolo} >= M_z,sd"
        valori = (
            Valore(simbolo=m_simbolo, valore=output.sezione.mpl_z_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="M_z,sd", valore=inputs.mz_sd_kNm, unita="kNm"),
        )
        nota = f"n={n:.4g} ≤ a={a:.4g}: nessuna riduzione per sforzo normale, eq. (6.39a)."
    else:
        simbolo = "M_N,Rd,z  (n > a)"
        formula = f"{m_simbolo} * (1 - ((n - min((A-2*b*t_f)/A,0.5)) / (1 - min((A-2*b*t_f)/A,0.5)))^2) >= M_z,sd"
        valori = (
            Valore(simbolo=m_simbolo, valore=output.sezione.mpl_z_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="n", valore=n, descrizione="calcolato sopra"),
            Valore(simbolo="A", valore=inputs.area_mm2, unita="mm2"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="t_f", valore=inputs.tf_mm, unita="mm"),
            Valore(simbolo="M_z,sd", valore=inputs.mz_sd_kNm, unita="kNm"),
        )
        nota = f"n={n:.4g} > a={a:.4g}: riduzione quadratica per sforzo normale, eq. (6.39b)."
    return Passo(
        simbolo=simbolo, formula=formula, valori=valori,
        risultato=interaz_semp.mn_rd_z_kNm, unita="kNm", clausola="EN1993-1-1 §6.2.9.1(5)",
        esito="soddisfatta" if interaz_semp.verifica_zz.passed else "non soddisfatta", nota=nota,
    )


def _passo_v54(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    interaz_semp = output.interazione_semplificata
    return Passo(
        simbolo="V54 (interazione lineare)",
        formula="n + M_y,sd/M_N,Rd,y + M_z,sd/M_N,Rd,z < 1",
        valori=(
            Valore(simbolo="n", valore=interaz_semp.n_ratio, descrizione="calcolato sopra"),
            Valore(simbolo="M_y,sd", valore=inputs.my_sd_kNm, unita="kNm"),
            Valore(simbolo="M_N,Rd,y", valore=interaz_semp.mn_rd_y_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="M_z,sd", valore=inputs.mz_sd_kNm, unita="kNm"),
            Valore(simbolo="M_N,Rd,z", valore=interaz_semp.mn_rd_z_kNm, unita="kNm", descrizione="calcolato sopra"),
        ),
        risultato=interaz_semp.v54, unita="-", clausola="EN1993-1-1 §6.2.9.1",
        esito="soddisfatta" if interaz_semp.verifica_lineare.passed else "non soddisfatta",
        nota="Somma lineare dei rapporti di utilizzo, verifica di riscontro rispetto all'interazione "
             "dell'Annex A.",
    )


def _passo_i56(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    interaz_semp = output.interazione_semplificata
    return Passo(
        simbolo="I56 (interazione a potenza)",
        formula="(M_y,sd/M_N,Rd,y)^2 + (M_z,sd/M_N,Rd,z)^max(5*n,1) < 1",
        valori=(
            Valore(simbolo="M_y,sd", valore=inputs.my_sd_kNm, unita="kNm"),
            Valore(simbolo="M_N,Rd,y", valore=interaz_semp.mn_rd_y_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="M_z,sd", valore=inputs.mz_sd_kNm, unita="kNm"),
            Valore(simbolo="M_N,Rd,z", valore=interaz_semp.mn_rd_z_kNm, unita="kNm", descrizione="calcolato sopra"),
            Valore(simbolo="n", valore=interaz_semp.n_ratio, descrizione="calcolato sopra"),
        ),
        risultato=interaz_semp.i56, unita="-", clausola="EN1993-1-1 §6.2.9.1(6) eq. (6.41)",
        esito="soddisfatta" if interaz_semp.verifica_potenza.passed else "non soddisfatta",
        nota="Interazione a potenza per sezioni a I/H, esponente 2 sull'asse forte e max(5n,1) sull'asse debole.",
    )

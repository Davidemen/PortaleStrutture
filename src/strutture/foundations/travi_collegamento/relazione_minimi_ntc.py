"""Verified restatement (docs/architecture-phase2.md) of `minimi_ntc.py` (NTC2018 §7.2.5, minimum
stirrup area check `Ast/p > Ast,min`, `shared.rebar_catalog.asw_per_m`). `d` reuses `geometria.
altezza_utile_mm` (H − cf), the same formula `ca_travi.relazione_geometria` already restates for a
different package."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import MM_PER_M

from .materiali import MaterialiResult
from .minimi_ntc import AST_MIN_PER_B_NTC, PMAX_ASSOLUTO_MM_NTC, PMAX_FRAZIONE_D_NTC, MinimiNtcResult
from .models import TraviCollegamentoInput

PI_GRECO = math.pi
CLAUSOLA = "NTC2018 §7.2.5"


def traccia_minimi_ntc(inputs: TraviCollegamentoInput, mat: MaterialiResult, min_: MinimiNtcResult) -> Traccia:
    """4 passi: d, pmax (informativo, nessun Check lo confronta con p), Ast,min, verifica area
    staffe (Check "Verifica area staffe")."""
    return Traccia(
        titolo="Staffe minime (NTC2018)",
        passi=(_passo_d(inputs, min_), _passo_pmax(min_), _passo_ast_min(inputs, min_), _passo_verifica(inputs, min_)),
    )


def _passo_d(inputs: TraviCollegamentoInput, min_: MinimiNtcResult) -> Passo:
    return Passo(
        simbolo="d", formula="H - c",
        valori=(
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="c", valore=inputs.cf_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=min_.d_mm, unita="mm",
        nota="Altezza utile della sezione.",
    )


def _passo_pmax(min_: MinimiNtcResult) -> Passo:
    return Passo(
        simbolo="p_max", formula=f"min({PMAX_FRAZIONE_D_NTC:g} * d, {PMAX_ASSOLUTO_MM_NTC:.6g})",
        valori=(Valore(simbolo="d", valore=min_.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),),
        risultato=min_.pmax_mm, unita="mm",
        nota=f"Passo massimo ammesso delle staffe: {PMAX_FRAZIONE_D_NTC:g}·d oppure il tetto assoluto di "
             f"{PMAX_ASSOLUTO_MM_NTC:.4g} mm (1000/3), il minore dei due. Valore informativo: nessun Check "
             "di questo foglio lo confronta con il passo p effettivamente adottato.",
    )


def _passo_ast_min(inputs: TraviCollegamentoInput, min_: MinimiNtcResult) -> Passo:
    return Passo(
        simbolo="A_st,min", formula=f"{AST_MIN_PER_B_NTC:g} * B",
        valori=(Valore(simbolo="B", valore=inputs.b_mm, unita="mm", descrizione="base della sezione"),),
        risultato=min_.ast_min_mm2_per_m, unita="mm2/m", clausola=CLAUSOLA,
        nota="Area minima di staffe trasversali per metro, per travi di collegamento.",
    )


def _passo_verifica(inputs: TraviCollegamentoInput, min_: MinimiNtcResult) -> Passo:
    densita_mm2_per_m = min_.verifica.value
    assert densita_mm2_per_m is not None
    soddisfatta = min_.verifica.passed
    return Passo(
        simbolo="A_st/p", formula=f"n_br * π * φ_st^2 / 4 * {MM_PER_M:g} / p > A_st,min",
        valori=(
            Valore(simbolo="n_br", valore=float(inputs.n_bracci), descrizione="numero di bracci delle staffe"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ_st", valore=inputs.phi_staffa_mm, unita="mm", descrizione="diametro delle staffe"),
            Valore(simbolo="p", valore=inputs.p_mm, unita="mm", descrizione="passo staffe considerato"),
            Valore(simbolo="A_st,min", valore=min_.ast_min_mm2_per_m, unita="mm2/m", descrizione="calcolato sopra"),
        ),
        risultato=densita_mm2_per_m, unita="mm2/m", clausola=min_.verifica.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Area di staffe effettivamente presente per metro di trave.",
    )

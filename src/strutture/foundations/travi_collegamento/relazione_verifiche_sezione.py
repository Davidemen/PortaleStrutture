"""Verified restatement (docs/architecture-phase2.md) of `compressione.py` (NTC2018/EN1998 §7.2.5,
`Nc,Rd = Ac·fcd`) and `trazione.py` (`Nt,Rd = As·fyd`), shared by both `norma` branches — the
caller passes the branch-appropriate clause (NTC2018 §7.2.5 or EN1998-5 §5.4.1.2). Both `N_PER_KN`
conversions are pure `scala` (mm²·MPa = N, ÷1000 = kN), never a bare literal in the formula
(docs/architecture-phase2.md §6 lesson 5). Standard mode only: `trazione.py`'s own
`legacy_compat=True` branch (comparing `Nt,Rd` against the *compression* work ratio, a sheet
copy-paste bug) never applies here — the comparison is always against `NEd`, as the fixed formula
below states."""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import N_PER_KN

from .azione import AzioneResult
from .compressione import CompressioneResult
from .materiali import MaterialiResult
from .trazione import TrazioneResult


def traccia_compressione(mat: MaterialiResult, az: AzioneResult, comp: CompressioneResult, clausola: str) -> Traccia:
    """2 passi: Nc,Rd, verifica (Check "Verifica a compressione", highlight η_c)."""
    return Traccia(titolo="Verifica a compressione", passi=(_passo_ncrd(mat, comp, clausola), _passo_verifica_compressione(az, comp, clausola)))


def _passo_ncrd(mat: MaterialiResult, comp: CompressioneResult, clausola: str) -> Passo:
    return Passo(
        simbolo="N_c,Rd", formula="A_c * f_cd",
        valori=(
            Valore(simbolo="A_c", valore=mat.ac_mm2, unita="mm2", descrizione="area della sezione di calcestruzzo, calcolata sopra"),
            Valore(simbolo="f_cd", valore=mat.fcd_MPa, unita="MPa", descrizione="tensione di calcolo a compressione del calcestruzzo, calcolata sopra"),
        ),
        risultato=comp.ncrd_kN, unita="kN", scala=1.0 / N_PER_KN, clausola=clausola,
        nota="Forza assiale resistente a compressione.",
    )


def _passo_verifica_compressione(az: AzioneResult, comp: CompressioneResult, clausola: str) -> Passo:
    """`clausola` è quella passata dal chiamante (NTC2018 §7.2.5 / EN1998-5 §5.4.1.2), non
    `comp.verifica.clause`: il `Check` di `compressione.py` cita sempre "NTC2018 §7.2.5" anche nel
    ramo EN1998 (stesso valore in entrambi i rami, solo l'etichetta non distingue la normativa)."""
    soddisfatta = comp.verifica.passed
    return Passo(
        simbolo="η_c", formula="N_Ed / N_c,Rd < 1",
        valori=(
            Valore(simbolo="N_Ed", valore=az.ned_kN, unita="kN", descrizione="forza assiale di progetto, calcolata sopra"),
            Valore(simbolo="N_c,Rd", valore=comp.ncrd_kN, unita="kN", descrizione="calcolato sopra"),
        ),
        risultato=comp.tasso_lavoro, unita="-", clausola=clausola,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di lavoro a compressione.",
    )


def traccia_trazione(mat: MaterialiResult, az: AzioneResult, traz: TrazioneResult, clausola: str) -> Traccia:
    """2 passi: Nt,Rd, verifica (Check "Verifica a trazione", highlight η_t)."""
    return Traccia(titolo="Verifica a trazione", passi=(_passo_ntrd(mat, traz, clausola), _passo_verifica_trazione(az, traz, clausola)))


def _passo_ntrd(mat: MaterialiResult, traz: TrazioneResult, clausola: str) -> Passo:
    return Passo(
        simbolo="N_t,Rd", formula="A_s * f_yd",
        valori=(
            Valore(simbolo="A_s", valore=mat.as_mm2, unita="mm2", descrizione="area delle barre longitudinali, calcolata sopra"),
            Valore(simbolo="f_yd", valore=mat.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio, calcolata sopra"),
        ),
        risultato=traz.ntrd_kN, unita="kN", scala=1.0 / N_PER_KN, clausola=clausola,
        nota="Forza assiale resistente a trazione.",
    )


def _passo_verifica_trazione(az: AzioneResult, traz: TrazioneResult, clausola: str) -> Passo:
    soddisfatta = traz.verifica.passed
    return Passo(
        simbolo="η_t", formula="N_Ed / N_t,Rd < 1",
        valori=(
            Valore(simbolo="N_Ed", valore=az.ned_kN, unita="kN", descrizione="forza assiale di progetto, calcolata sopra"),
            Valore(simbolo="N_t,Rd", valore=traz.ntrd_kN, unita="kN", descrizione="calcolato sopra"),
        ),
        risultato=traz.tasso_lavoro, unita="-", clausola=clausola,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di lavoro a trazione (modalità standard: confrontato contro NEd, non contro il "
             "tasso di lavoro a compressione — review finding WRONG_COMPARISON del foglio originale).",
    )

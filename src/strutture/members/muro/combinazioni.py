"""Partial factors per combination row (muro-sostegno rows 45-50 static, 80-81 seismic).

Every (γG,muro, γφ,terr, γG,terr, γQ) tuple below was cross-checked directly against the
workbook (`Muro di sostegno DM2018.xlsx`, sheet Tratto A, columns D/J/N/C of rows 45-50/80-81,
read with openpyxl) rather than trusting the spec's transcription (docs/specs/muro-sostegno.md
Tool 1's table understates γQ for GEO_1/EQU_1 as 0 when the sheet has 1.3/1.5 — see
docs/divergences/muro-sostegno.md). Each row picks one NTC2018 Tab. 6.2.I approccio (EQU/A1/A2)
and, independently, a favorevole/sfavorevole selection for the wall self-weight, the backfill
self-weight and the surcharge Q — the three are not always the same choice within one row (e.g.
EQU_1 takes γG1 favorevole for the wall but γG1/γQ sfavorevole for the backfill/surcharge, since
the wall's own weight always stabilises the overturning check while the backfill/surcharge are
treated as the adverse action). Seismic rows use Approccio 2 (A2+M2) per the sheet's own note at
row 76 ("si deve utilizzare la combinazione A2-M2"); their γQ=0.6 is the seismic combination
factor (NTC2018 §2.5.3), not a Tab. 6.2.I entry, so it is a fixed value, not a favorevole/
sfavorevole selection.
"""
from typing import Literal, NamedTuple

from strutture.shared.ntc_combos import (
    ApproccioAzioni,
    ApproccioGeotecnico,
    FattoriAzioni,
    fattori_azioni,
    fattori_geotecnici,
)

from .models import NomeCombo

STATIC_COMBOS: tuple[NomeCombo, ...] = ("STR_1", "STR_2", "GEO_1", "GEO_2", "EQU_1", "EQU_2")
SEISMIC_COMBOS: tuple[NomeCombo, ...] = ("SISMA_1", "SISMA_2")
ALL_COMBOS: tuple[NomeCombo, ...] = STATIC_COMBOS + SEISMIC_COMBOS

_Selezione = Literal["favorevole", "sfavorevole"]
GAMMA_Q_SISMICO = 0.6  # NTC2018 §2.5.3 — coefficiente di combinazione sismica (rows 87/88, col C)


class _Definizione(NamedTuple):
    approccio_azioni: ApproccioAzioni
    approccio_geotecnico: ApproccioGeotecnico
    selezione_muro: _Selezione
    selezione_terr: _Selezione
    selezione_q: _Selezione | None  # None -> GAMMA_Q_SISMICO is used instead


_DEFINIZIONI: dict[NomeCombo, _Definizione] = {
    "STR_1": _Definizione("A1", "M1", "sfavorevole", "sfavorevole", "sfavorevole"),
    "STR_2": _Definizione("A1", "M1", "favorevole", "favorevole", "favorevole"),
    "GEO_1": _Definizione("A2", "M2", "sfavorevole", "sfavorevole", "sfavorevole"),
    "GEO_2": _Definizione("A2", "M2", "favorevole", "favorevole", "favorevole"),
    "EQU_1": _Definizione("EQU", "M2", "favorevole", "sfavorevole", "sfavorevole"),
    "EQU_2": _Definizione("EQU", "M2", "favorevole", "sfavorevole", "favorevole"),
    "SISMA_1": _Definizione("A2", "M2", "favorevole", "favorevole", None),
    "SISMA_2": _Definizione("A2", "M2", "favorevole", "favorevole", None),
}


class FattoriCombo(NamedTuple):
    gamma_g_muro: float
    gamma_phi_terr: float
    gamma_g_terr: float
    gamma_q: float


def _gamma_g1(azioni: FattoriAzioni, selezione: _Selezione) -> float:
    return azioni.gamma_g1_favorevole if selezione == "favorevole" else azioni.gamma_g1_sfavorevole


def _gamma_q(azioni: FattoriAzioni, selezione: _Selezione | None) -> float:
    if selezione is None:
        return GAMMA_Q_SISMICO
    return azioni.gamma_q_favorevole if selezione == "favorevole" else azioni.gamma_q_sfavorevole


def fattori_combo(nome: NomeCombo, *, legacy_compat: bool = False) -> FattoriCombo:
    """Partial factors (γG,muro / γφ,terr / γG,terr / γQ) for one combination row.

    `legacy_compat` is accepted for interface consistency with the rest of the codebase but does
    not change this function's result: every factor below is confirmed identical between the
    sheet and NTC Tab. 6.2.I/6.2.II (see module docstring and docs/divergences/muro-sostegno.md).
    """
    del legacy_compat
    definizione = _DEFINIZIONI[nome]
    azioni = fattori_azioni(definizione.approccio_azioni)
    geotecnici = fattori_geotecnici(definizione.approccio_geotecnico)
    return FattoriCombo(
        gamma_g_muro=_gamma_g1(azioni, definizione.selezione_muro),
        gamma_phi_terr=geotecnici.gamma_tan_phi,
        gamma_g_terr=_gamma_g1(azioni, definizione.selezione_terr),
        gamma_q=_gamma_q(azioni, definizione.selezione_q),
    )

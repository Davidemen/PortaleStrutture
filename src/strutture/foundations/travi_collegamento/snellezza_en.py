"""Slenderness check, EN sheet variant (C39:C44) — EN1992-1-1 §5.8.3.1 buckling-curve style
formula `λlim = 20·A·B·C/sqrt(n)`, with `A=0.7` (assumed φef unknown), `B=sqrt(1+2ω)`, `C=0.7`
(assumed rm=1 -> C=1.7-rm=0.7) pre-baked as sheet literals rather than computed from φef/rm inputs.
"""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import CalcError, Check
from strutture.shared.units import N_PER_KN

from .geometria import raggio_inerzia_debole_mm

LAMBDA_LIM_BASE_EC2 = 20.0  # EN1992-1-1 §5.8.3.1 eq. 5.13N base coefficient.
LAMBDA_LIM_A_ASSUNTO = 0.7  # A = 1/(1+0.2*φef), assumed (φef not given on the sheet).
LAMBDA_LIM_C_ASSUNTO = 0.7  # C = 1.7 - rm, assumed rm=1 (single-curvature default).


class SnellezzaEnResult(BaseModel):
    """l0, i, ω, λ, λlim, verifica, tasso di lavoro."""

    model_config = ConfigDict(frozen=True)

    l0_mm: float = Field(description="Lunghezza di libera inflessione l0", json_schema_extra={"unit": "mm", "symbol": "l_0"}, gt=0)
    i_mm: float = Field(description="Raggio d'inerzia i", json_schema_extra={"unit": "mm", "symbol": "i"}, gt=0)
    omega: float = Field(description="Rapporto meccanico di armatura ω", json_schema_extra={"unit": "-", "symbol": "ω"}, ge=0)
    lambda_: float = Field(description="Snellezza della trave di collegamento λ", json_schema_extra={"unit": "-", "symbol": "λ"}, gt=0)
    lambda_lim: float = Field(description="Snellezza limite λlim", json_schema_extra={"unit": "-", "symbol": "λ_lim"}, gt=0)
    verifica: Check
    tasso_lavoro: float = Field(description="Tasso di lavoro λ/λlim", json_schema_extra={"unit": "-"}, ge=0)


def snellezza_en(
    b_mm: float, h_mm: float, l_mm: float, beta: float, ned_kN: float,
    ac_mm2: float, fcd_MPa: float, as_mm2: float, fyd_MPa: float,
) -> SnellezzaEnResult:
    """l0[C38], i[C39], ω[C40], λ[C41], λlim[C42]; verifica: λlim > λ.

    NEd=0 (soil A under EN1998, α=0 — EN1998-5 §5.4.1.2 point 5: tie beams not required for
    ground type A) makes the sheet's `λlim` formula divide by zero (`#DIV/0!`); the buckling
    check is not meaningful without an axial force, so this is reported as an input error.
    """
    if ned_kN <= 0:
        raise CalcError(
            "La verifica di snellezza richiede una forza assiale di progetto NEd > 0 "
            "(su terreno A la normativa EN1998 non richiede travi di collegamento, α=0)"
        )
    l0_mm = l_mm * beta
    i_mm = raggio_inerzia_debole_mm(b_mm, h_mm)
    omega = as_mm2 * fyd_MPa / (ac_mm2 * fcd_MPa)
    lambda_ = l0_mm / i_mm
    n_adimensionale = ned_kN * N_PER_KN / (ac_mm2 * fcd_MPa)
    lambda_lim = (
        LAMBDA_LIM_BASE_EC2 * LAMBDA_LIM_A_ASSUNTO * math.sqrt(1 + 2 * omega) * LAMBDA_LIM_C_ASSUNTO
        / math.sqrt(n_adimensionale)
    )
    return SnellezzaEnResult(
        l0_mm=l0_mm, i_mm=i_mm, omega=omega, lambda_=lambda_, lambda_lim=lambda_lim,
        verifica=Check(name="Verifica snellezza", passed=lambda_lim > lambda_, clause="EN1992-1-1 §5.8.3.1", value=lambda_, limit=lambda_lim, unit="-"),
        tasso_lavoro=lambda_ / lambda_lim,
    )

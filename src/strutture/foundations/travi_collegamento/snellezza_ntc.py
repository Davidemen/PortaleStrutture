"""Slenderness check, NTC sheet variant (C40:C45): `λlim = 25/sqrt(NEd·1000/(Ac·fcd))`.

Label/formula note (spec "Suspected spreadsheet bugs" #4): the sheet's row label reads
"λ > λlim" but the formula actually tests `λlim > λ` — the label is cosmetic and swapped, the
comparison direction below matches the formula (values are correct), not the label text.
"""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import CalcError, Check
from strutture.shared.units import N_PER_KN

from .geometria import raggio_inerzia_debole_mm

# NTC2018 §7.2.5 empirical slenderness-limit coefficient (buckling check, sheet C43).
LAMBDA_LIM_COEFFICIENTE_NTC = 25.0


class SnellezzaNtcResult(BaseModel):
    """l0, i, λ, λlim, verifica, tasso di lavoro."""

    model_config = ConfigDict(frozen=True)

    l0_mm: float = Field(description="Lunghezza di libera inflessione l0", json_schema_extra={"unit": "mm", "symbol": "l_0"}, gt=0)
    i_mm: float = Field(description="Raggio d'inerzia i", json_schema_extra={"unit": "mm", "symbol": "i"}, gt=0)
    lambda_: float = Field(description="Snellezza della trave di collegamento λ", json_schema_extra={"unit": "-", "symbol": "λ"}, gt=0)
    lambda_lim: float = Field(description="Snellezza limite λlim", json_schema_extra={"unit": "-", "symbol": "λ_lim"}, gt=0)
    verifica: Check
    tasso_lavoro: float = Field(description="Tasso di lavoro λ/λlim", json_schema_extra={"unit": "-"}, ge=0)


def snellezza_ntc(b_mm: float, h_mm: float, l_mm: float, beta: float, ned_kN: float, ac_mm2: float, fcd_MPa: float) -> SnellezzaNtcResult:
    """l0[C40], i[C41], λ[C42], λlim[C43]; verifica: λlim > λ."""
    if ned_kN <= 0:
        raise CalcError("La verifica di snellezza richiede una forza assiale di progetto NEd > 0")
    l0_mm = l_mm * beta
    i_mm = raggio_inerzia_debole_mm(b_mm, h_mm)
    lambda_ = l0_mm / i_mm
    lambda_lim = LAMBDA_LIM_COEFFICIENTE_NTC / math.sqrt(ned_kN * N_PER_KN / (ac_mm2 * fcd_MPa))
    return SnellezzaNtcResult(
        l0_mm=l0_mm, i_mm=i_mm, lambda_=lambda_, lambda_lim=lambda_lim,
        verifica=Check(name="Verifica snellezza", passed=lambda_lim > lambda_, clause="NTC2018 §7.2.5", value=lambda_, limit=lambda_lim, unit="-"),
        tasso_lavoro=lambda_ / lambda_lim,
    )

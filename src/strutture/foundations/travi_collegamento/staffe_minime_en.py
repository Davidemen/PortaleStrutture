"""Minimum stirrup ratio, EN sheet variant (C58:C65) — EC2 §9.2.2 min shear-reinforcement ratio
formula (uses the characteristic yield fyk, not the design fyd — the spec's constants table names
`fyd` but the sheet formula `=0.08*SQRT(fck)/VLOOKUP(class_s,...,2,FALSE)` reads column 2 of the
rebar table, i.e. raw fyk, matching EC2 §9.2.2 eq. 9.5N's `ρw,min = 0.08·sqrt(fck)/fyk`), and the
EC2-style max spacing rule (vs the NTC sheet's `0.8d` rule)."""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

from .geometria import altezza_utile_mm

PMAX_FRAZIONE_D_EC2 = 0.75  # EC2 §9.2.2 max stirrup spacing rule, coefficient on d.
PMAX_ASSOLUTO_MM_EC2 = 600.0  # EC2 §9.2.2 — limite assoluto passo staffe.
RHO_MIN_COEFFICIENTE_EC2 = 0.08  # EC2 §9.2.2 eq. 9.5N — coefficiente percentuale minima staffe.


class StaffeMinimeEnResult(BaseModel):
    """d, pmax, ρ, ρmin, verifica."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile d", json_schema_extra={"unit": "mm", "symbol": "d"}, gt=0)
    pmax_mm: float = Field(description="Passo staffe massimo pmax", json_schema_extra={"unit": "mm"}, gt=0)
    rho: float = Field(description="Percentuale armatura a staffe ρ", json_schema_extra={"unit": "-", "symbol": "ρ"}, gt=0)
    rho_min: float = Field(description="Percentuale minima staffe ρmin", json_schema_extra={"unit": "-", "symbol": "ρ_min"}, gt=0)
    verifica: Check


def staffe_minime_en(
    b_mm: float, h_mm: float, cf_mm: float, phi_staffa_mm: float, n_bracci: int, p_mm: float,
    alpha_staffa_deg: float, fck_MPa: float, fyk_MPa: float,
) -> StaffeMinimeEnResult:
    """d[C60], pmax[C61], ρmin[C63], ρ[C64]; verifica: ρ > ρmin."""
    d_mm = altezza_utile_mm(h_mm, cf_mm)
    pmax_mm = min(PMAX_FRAZIONE_D_EC2 * d_mm * (1 + 1 / math.tan(math.radians(alpha_staffa_deg))), PMAX_ASSOLUTO_MM_EC2)
    rho_min = RHO_MIN_COEFFICIENTE_EC2 * math.sqrt(fck_MPa) / fyk_MPa
    rho = math.pi * phi_staffa_mm**2 / 4.0 * n_bracci / (b_mm * p_mm)
    return StaffeMinimeEnResult(
        d_mm=d_mm, pmax_mm=pmax_mm, rho=rho, rho_min=rho_min,
        verifica=Check(name="Verifica area staffe", passed=rho > rho_min, clause="EC2 §9.2.2", value=rho, limit=rho_min, unit="-"),
    )

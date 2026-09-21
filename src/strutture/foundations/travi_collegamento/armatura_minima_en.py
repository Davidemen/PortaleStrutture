"""Minimum longitudinal reinforcement ratio, EN1998-1 §5.8.2(4) (sheet C47:C48)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

RHO_B_MIN_EN1998 = 0.008  # EN1998-1 §5.8.2(4) — area minima di armatura longitudinale, 0.8% di Ac.


class ArmaturaMinimaEnResult(BaseModel):
    """ρb, verifica."""

    model_config = ConfigDict(frozen=True)

    rho_b_mm2: float = Field(description="Area minima di armatura longitudinale ρb", json_schema_extra={"unit": "mm2", "symbol": "ρ_b"}, gt=0)
    verifica: Check


def armatura_minima_en(ac_mm2: float, as_mm2: float) -> ArmaturaMinimaEnResult:
    """ρb[C47] = 0.008·Ac; verifica: ρb < As[C48]."""
    rho_b_mm2 = RHO_B_MIN_EN1998 * ac_mm2
    return ArmaturaMinimaEnResult(
        rho_b_mm2=rho_b_mm2,
        verifica=Check(name="Verifica armatura longitudinale minima", passed=rho_b_mm2 < as_mm2, clause="EN1998-1 §5.8.2(4)", value=as_mm2, limit=rho_b_mm2, unit="mm2"),
    )

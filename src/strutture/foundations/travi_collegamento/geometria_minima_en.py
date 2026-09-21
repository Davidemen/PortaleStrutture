"""Minimum section geometry, EN1998-1/Rif.Normativi items 2-3 (sheet C49:C53)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

BW_MIN_MM_EN1998 = 250.0  # Rif.Normativi item 2 — base minima della trave di collegamento.
N_PIANI_SOGLIA_HW = 3  # Rif.Normativi item 3 — soglia numero di piani per hw,min.
HW_MIN_MM_BASSO = 400.0  # hw,min quando N.piani <= 3.
HW_MIN_MM_ALTO = 500.0  # hw,min quando N.piani > 3.


class GeometriaMinimaEnResult(BaseModel):
    """bw,min, hw,min, verifiche."""

    model_config = ConfigDict(frozen=True)

    bw_min_mm: float = Field(description="Base minima della trave di collegamento bw,min", json_schema_extra={"unit": "mm", "symbol": "b_w,min"}, gt=0)
    verifica_base: Check
    hw_min_mm: float = Field(description="Altezza minima della trave di collegamento hw,min", json_schema_extra={"unit": "mm", "symbol": "h_w,min"}, gt=0)
    verifica_altezza: Check


def geometria_minima_en(b_mm: float, h_mm: float, n_piani: int) -> GeometriaMinimaEnResult:
    """bw,min[C50]; verifica: bw,min < B[C51]. hw,min[C52]; verifica: hw,min <= H[C53]."""
    hw_min_mm = HW_MIN_MM_BASSO if n_piani <= N_PIANI_SOGLIA_HW else HW_MIN_MM_ALTO
    return GeometriaMinimaEnResult(
        bw_min_mm=BW_MIN_MM_EN1998,
        verifica_base=Check(name="Verifica base minima", passed=BW_MIN_MM_EN1998 < b_mm, clause="EN1998-1", value=b_mm, limit=BW_MIN_MM_EN1998, unit="mm"),
        hw_min_mm=hw_min_mm,
        verifica_altezza=Check(name="Verifica altezza minima", passed=hw_min_mm <= h_mm, clause="EN1998-1", value=h_mm, limit=hw_min_mm, unit="mm"),
    )

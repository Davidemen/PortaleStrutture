"""Contact-patch geometry for `pav-carichi-concentrati` (spec calculation steps 1-2): Westergaard's
equivalent-radius correction for a rectangular tyre footprint."""
import math

from pydantic import BaseModel, ConfigDict, Field

from .tables import RADIUS_CORRECTION_THRESHOLD


class ContattoResult(BaseModel):
    """`pav-carichi-concentrati` outputs L11/L12/L13 (contact geometry)."""

    model_config = ConfigDict(frozen=True)

    ac_mm2: float = Field(description="Area di contatto Ac = bx*by", gt=0, json_schema_extra={"unit": "mm2", "symbol": "A_c"})
    rr_mm: float = Field(description="Raggio equivalente di contatto rr = sqrt(Ac/pi)", gt=0, json_schema_extra={"unit": "mm", "symbol": "r_r"})
    b_mm: float = Field(description="Raggio di contatto corretto (Westergaard) b", gt=0, json_schema_extra={"unit": "mm", "symbol": "b"})


def contatto(impronta_a_mm: float, impronta_b_mm: float, h_mm: float) -> ContattoResult:
    """spec steps 1-2."""
    ac_mm2 = impronta_a_mm * impronta_b_mm
    rr_mm = math.sqrt(ac_mm2 / math.pi)
    if rr_mm / h_mm < RADIUS_CORRECTION_THRESHOLD:
        b_mm = math.sqrt(1.6 * rr_mm**2 + h_mm**2) - 0.675 * h_mm
    else:
        b_mm = rr_mm
    return ContattoResult(ac_mm2=ac_mm2, rr_mm=rr_mm, b_mm=b_mm)

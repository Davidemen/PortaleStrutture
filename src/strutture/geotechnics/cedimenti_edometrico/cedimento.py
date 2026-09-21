"""Step 7: total settlement — the cumulative ΣΔH,i of the last depth slice below Z,crit
(docs/specs/geo-cedimenti-edometrico.md, calculation step 3: `B15[wed(f)] = MAX(M3:M503)`). The
sheet's reset-to-0-past-cutoff idiom is not reproduced (see `righe.py`); this just reads the
running cumulative column at the cutoff depth, which is the same number."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.units import cm_to_mm

from .righe import RigaResult


class CedimentoResult(BaseModel):
    """Total oedometric settlement, in both cm (sheet unit) and mm."""

    model_config = ConfigDict(frozen=True)

    w_ed_cm: float = Field(description="Cedimento edometrico totale", json_schema_extra={"unit": "cm", "symbol": "w_ed", "highlight": True})
    w_ed_mm: float = Field(description="Cedimento edometrico totale", json_schema_extra={"unit": "mm", "symbol": "w_ed"})


def cedimento_totale(righe: tuple[RigaResult, ...], z_crit_utilizzato_m: float) -> CedimentoResult:
    """Cumulative settlement of the last row with `z_m < z_crit_utilizzato_m` (0 when `Z,crit`
    falls at or below the first slice)."""
    coperte = tuple(riga for riga in righe if riga.z_m < z_crit_utilizzato_m)
    w_ed_cm = coperte[-1].cumulativo_cm if coperte else 0.0
    return CedimentoResult(w_ed_cm=w_ed_cm, w_ed_mm=cm_to_mm(w_ed_cm))

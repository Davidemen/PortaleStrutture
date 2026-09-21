"""Pile coordinates + the sheet's grid schema (docs/architecture-batch2.md §1.2, §9-D5).

`schema_pali` names the rectangular grid as `#X`x`#Y` (sheet `Footing check!AM23`
"Case 1".."Case 4": 2x2, 2x1, 1x2, 1x1) so the enum reads directly as pile counts along X/Y."""
from typing import Literal

from pydantic import ConfigDict, Field

from strutture.shared.tabular import RowModel

SchemaPali = Literal["2x2", "2x1", "1x2", "1x1"]


class PilePos(RowModel):
    """One pile's plan coordinate, relative to the group centroid (m)."""

    model_config = ConfigDict(frozen=True)

    x_m: float = Field(description="Ascissa del palo rispetto al baricentro del gruppo", json_schema_extra={"unit": "m"})
    y_m: float = Field(description="Ordinata del palo rispetto al baricentro del gruppo", json_schema_extra={"unit": "m"})

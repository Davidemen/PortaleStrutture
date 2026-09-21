"""Frozen result model for `under_point` (docs/architecture-batch2.md §1.2)."""
from pydantic import BaseModel, ConfigDict, Field


class PointStress(BaseModel):
    """Vertical stress increase at an arbitrary point, decomposed into 4 signed sub-rectangle
    contributions (Fadum superposition, see `point.py`). `parts` sums to `total`; a part is
    negative when the corresponding sub-rectangle lies outside the loaded footprint."""

    model_config = ConfigDict(frozen=True)

    total: float = Field(description="Incremento di tensione verticale Δσz nel punto", json_schema_extra={"unit": "kPa"})
    parts: tuple[float, float, float, float] = Field(
        description="Contributi segnati dei 4 sotto-rettangoli (Fadum)", json_schema_extra={"unit": "kPa"}
    )

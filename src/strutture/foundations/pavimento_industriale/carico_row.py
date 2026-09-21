"""Row of the `carichi` table (architecture-batch2.md §2): one concentrated ("wheel") load in one
slab position. Replaces the sheet's two fixed column-blocks (`K:O` "ruota motrice", `Q:U` "ruote
anteriori", each with 3 position sub-columns `L/M/N`) with rows — any number of load cases, and
`gamma`/`psi1` become per-row columns instead of the sheet's `$L$6`/`$M$6` absolute references
(architecture-batch2.md §7 `pavimento $L$6`, fixed by construction: a row can't "leak" another
row's column)."""
from typing import Literal

from pydantic import Field

from strutture.shared.tabular import RowModel

PosizioneCarico = Literal["centro", "bordo", "spigolo"]


class CaricoRow(RowModel):
    """One row of the `carichi` input table (max 12 rows, architecture-batch2.md §2)."""

    caso: str = Field(description="Nome del caso di carico (es. 'ruota motrice')", max_length=64, json_schema_extra={"group": "Carichi concentrati"})
    posizione: PosizioneCarico = Field(description="Posizione del carico sulla piastra", json_schema_extra={"symbol": "pos", "group": "Carichi concentrati"})
    p_kN: float = Field(description="Carico concentrato (ruota) P", gt=0, le=1000, json_schema_extra={"unit": "kN", "symbol": "P", "group": "Carichi concentrati"})
    impronta_a_mm: float = Field(description="Impronta di carico, dimensione x", gt=0, le=2000, json_schema_extra={"unit": "mm", "symbol": "b_x", "group": "Carichi concentrati"})
    impronta_b_mm: float = Field(description="Impronta di carico, dimensione y", gt=0, le=2000, json_schema_extra={"unit": "mm", "symbol": "b_y", "group": "Carichi concentrati"})
    gamma: float = Field(description="Coefficiente parziale del carico", gt=0, le=3, json_schema_extra={"symbol": "γ", "group": "Carichi concentrati"})
    psi1: float = Field(description="Coefficiente di combinazione frequente ψ1", gt=0, le=1, json_schema_extra={"symbol": "ψ_1", "group": "Carichi concentrati"})

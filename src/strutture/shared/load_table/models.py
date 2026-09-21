"""Row + result models for the support-reactions table (docs/architecture-batch2.md §1.2, §2).

`ReactionRow` is what a `reazioni` table field (isolated footings, pile caps) holds: one row per
(nodo, combo). `famiglia` is the code-standard replacement for the sheet's hard-coded combo
row-ranges (`INPUT!AE4:AG10`) — it is optional because the pile-cap workbook has no family split
(`None` -> one global envelope, per §2 table)."""
from typing import Literal

from pydantic import ConfigDict, Field

from strutture.shared.tabular import RowModel

# Combination families as used by the isolated-footing envelope (§1.2, §7 "AE4:AG10"); ULS/SLV/SLE
# per NTC2018 §2.5.3 / §3.2.5; STR/EQU/RARA/FREQ/QP name the sub-case.
Famiglia = Literal["SLU_STR", "SLU_EQU", "SLV_STR", "SLV_EQU", "SLE_RARA", "SLE_FREQ", "SLE_QP"]


class ReactionRow(RowModel):
    """One (nodo, combo) support reaction, MIDAS/Excel-export column order (§2 `reazioni` table)."""

    model_config = ConfigDict(frozen=True)

    nodo: int = Field(description="Nodo della struttura", ge=1, json_schema_extra={"unit": "-", "aliases": ["Node", "Nodo", "NODE"]})
    combo: str = Field(
        description="Nome della combinazione di carico (LCC)",
        min_length=1,
        max_length=64,
        json_schema_extra={"unit": "-", "aliases": ["LCC", "Combo", "Load Case", "Combination"]},
    )
    famiglia: Famiglia | None = Field(
        default=None,
        description="Famiglia della combinazione (assente = un solo inviluppo globale)",
        json_schema_extra={"unit": "-", "aliases": ["Famiglia", "Family", "Group"]},
    )
    fx_kN: float = Field(description="Reazione orizzontale Fx", json_schema_extra={"unit": "kN", "aliases": ["Fx", "FX", "Fx (kN)"]})
    fy_kN: float = Field(description="Reazione orizzontale Fy", json_schema_extra={"unit": "kN", "aliases": ["Fy", "FY", "Fy (kN)"]})
    fz_kN: float = Field(description="Reazione verticale Fz (N)", json_schema_extra={"unit": "kN", "aliases": ["Fz", "FZ", "N", "Fz (kN)"]})
    mx_kNm: float = Field(description="Momento Mx", json_schema_extra={"unit": "kNm", "aliases": ["Mx", "MX", "Mx (kNm)"]})
    my_kNm: float = Field(description="Momento My", json_schema_extra={"unit": "kNm", "aliases": ["My", "MY", "My (kNm)"]})
    mz_kNm: float = Field(description="Momento Mz", json_schema_extra={"unit": "kNm", "aliases": ["Mz", "MZ", "Mz (kNm)"]})


EnvelopeMode = Literal["max", "min", "absmax"]


class EnvelopeRow(RowModel):
    """One inviluppo cell: the governing value of a quantity (+ the row that produced it), per §2
    `inviluppo: tuple[EnvelopeRow, ...]` contract. `indice` is the 0-based position of the governing
    row inside the sequence passed to `envelope`/`governing`."""

    model_config = ConfigDict(frozen=True)

    famiglia: Famiglia | None = Field(description="Famiglia dell'inviluppo (None = tutte le righe)", json_schema_extra={"unit": "-"})
    valore: float = Field(description="Valore governante della grandezza", json_schema_extra={"unit": "-"})
    combo: str = Field(description="Combinazione governante", json_schema_extra={"unit": "-"})
    nodo: int = Field(description="Nodo della riga governante", json_schema_extra={"unit": "-"})
    indice: int = Field(description="Posizione (0-based) della riga governante nella tabella", ge=0, json_schema_extra={"unit": "-"})

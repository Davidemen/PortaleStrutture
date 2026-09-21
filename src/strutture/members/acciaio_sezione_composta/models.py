"""Input model for `acciaio-sezione-h-rimpiattata` (Rev00/Rev01 — H/I profile + welded plates).

Sheet layout: an H/I profile (top flange, web, bottom flange) reinforced with up to two flat
plates welded to the flange tips (rows A4/A5). Generalised here to a `piatti` table of up to 10
independent plates (architecture-batch2.md §2): each row is `b_mm` (plate thickness) / `h_mm`
(plate height); `b_mm=0` disables the row. `legacy_compat=True` caps the table at the sheet's two
physical plate slots and reproduces its exact placement/centroid formulas, bugs included.
"""
from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.divergences import legacy
from strutture.shared.tabular import RowModel, table_field

MAX_PIATTI = 10
LEGACY_MAX_PIATTI = 2  # sheet rows A4/A5


class PiattoRow(RowModel):
    """One reinforcing flat plate welded to a flange tip."""

    b_mm: float = Field(default=0.0, ge=0, description="Spessore piatto b (0 = piatto assente)",
                         json_schema_extra={"unit": "mm", "symbol": "b"})
    h_mm: float = Field(default=0.0, ge=0, description="Altezza piatto h",
                         json_schema_extra={"unit": "mm", "symbol": "h"})


class SezioneHRimpiattataInput(BaseModel):
    """`Rev00`/`Rev01` — geometria del profilo H base più i piatti di rinforzo saldati."""

    model_config = ConfigDict(frozen=True)

    h_profilo_mm: float = Field(description="Altezza totale del profilo base H (B1)", gt=0, le=5000,
                                 json_schema_extra={"unit": "mm", "symbol": "H", "group": "Profilo base"})
    b_profilo_mm: float = Field(description="Larghezza delle ali del profilo base B (B2/B6)", gt=0, le=2000,
                                 json_schema_extra={"unit": "mm", "symbol": "B", "group": "Profilo base"})
    tf_mm: float = Field(description="Spessore delle ali tf (C6)", gt=0, le=200,
                          json_schema_extra={"unit": "mm", "symbol": "t_f", "group": "Profilo base"})
    tw_mm: float = Field(description="Spessore dell'anima tw (B7)", gt=0, le=200,
                          json_schema_extra={"unit": "mm", "symbol": "t_w", "group": "Profilo base"})
    piatti: tuple[PiattoRow, ...] = table_field(
        PiattoRow, max_rows=MAX_PIATTI, min_rows=0,
        description="Piatti di rinforzo saldati alle estremità delle ali (A4, A5, ...)",
        fixed_rows=False,
    )
    legacy_compat: bool = Field(default=False, description="Riproduce esattamente il foglio Excel (bug inclusi)",
                                 json_schema_extra={"advanced": True})

    @model_validator(mode="after")
    def _validazione(self) -> "SezioneHRimpiattataInput":
        if 2.0 * self.tf_mm >= self.h_profilo_mm:
            raise ValueError(f"tf_mm ({self.tf_mm}) deve essere minore della metà di h_profilo_mm ({self.h_profilo_mm})")
        if legacy("acciaio-sezione-h-rimpiattata/legacy-max-due-piatti", self.legacy_compat) and len(self.piatti) > LEGACY_MAX_PIATTI:
            raise ValueError(f"legacy_compat=True: al più {LEGACY_MAX_PIATTI} piatti (righe fisse A4/A5 del foglio)")
        return self

"""Step: per-family envelope of every governing quantity (docs/architecture-batch2.md §2 `inviluppo`;
docs/specs/fond-plinti-isolati.md Tool-2 steps 3-5) + the sheet's own asymmetry: the eccentricity
envelope mixes every family together (Tool-2 step 6, `INPUT!T34:T37`) instead of splitting by
`famiglia` like every other quantity here."""
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.load_table import EnvelopeRow, Famiglia, envelope, governing

from .riga_verifica import RigaVerifica

Grandezza = Literal["pressione_max_kpa", "area_compressa_min", "ribaltamento_x_min", "ribaltamento_y_min",
                     "scorrimento_min"]

# (grandezza, estrattore, modalita di inviluppo) — docs/specs/fond-plinti-isolati.md Tool-1 outputs.
_QUANTITA: tuple[tuple[Grandezza, Callable[[RigaVerifica], float | None], str], ...] = (
    ("pressione_max_kpa", lambda r: r.sigma_max_kpa, "max"),
    ("area_compressa_min", lambda r: r.compressed_ratio, "min"),
    ("ribaltamento_x_min", lambda r: r.mu_ribaltamento_x, "min"),
    ("ribaltamento_y_min", lambda r: r.mu_ribaltamento_y, "min"),
    ("scorrimento_min", lambda r: r.mu_scorrimento, "min"),
)


class InviluppoRiga(BaseModel):
    """One (grandezza, famiglia) envelope cell: the governing value and its combo/nodo."""

    model_config = ConfigDict(frozen=True)

    grandezza: Grandezza = Field(description="Grandezza inviluppata", json_schema_extra={"unit": "-"})
    famiglia: Famiglia | None = Field(description="Famiglia della combinazione governante", json_schema_extra={"unit": "-"})
    valore: float = Field(description="Valore governante", json_schema_extra={"unit": "-"})
    combo: str = Field(description="Combinazione governante", json_schema_extra={"unit": "-"})
    nodo: int = Field(description="Nodo della combinazione governante", json_schema_extra={"unit": "-"})


class Eccentricita(BaseModel):
    """Global eccentricity envelope over every row, mixing all families (sheet asymmetry, kept as-is:
    docs/architecture-batch2.md §7 `plinti-isolati` global eccentricity note)."""

    model_config = ConfigDict(frozen=True)

    ex_max: EnvelopeRow = Field(description="Eccentricità massima lungo X, su tutte le combinazioni")
    ex_min: EnvelopeRow = Field(description="Eccentricità minima lungo X, su tutte le combinazioni")
    ey_max: EnvelopeRow = Field(description="Eccentricità massima lungo Y, su tutte le combinazioni")
    ey_min: EnvelopeRow = Field(description="Eccentricità minima lungo Y, su tutte le combinazioni")


def inviluppo(righe: tuple[RigaVerifica, ...]) -> tuple[InviluppoRiga, ...]:
    """One `InviluppoRiga` per (grandezza, famiglia) with a defined governing row."""
    result: tuple[InviluppoRiga, ...] = ()
    for grandezza, value, mode in _QUANTITA:
        for env_row in envelope(righe, value, mode, by="famiglia"):  # type: ignore[arg-type]
            result = (*result, InviluppoRiga(grandezza=grandezza, famiglia=env_row.famiglia,
                                              valore=env_row.valore, combo=env_row.combo, nodo=env_row.nodo))
    return result


def eccentricita_globale(righe: tuple[RigaVerifica, ...]) -> Eccentricita:
    """Global ex/ey max/min over every row (all families mixed, matching `INPUT!T34:T37`)."""
    ex_max = governing(righe, lambda r: r.ex_m, "max")  # type: ignore[arg-type]
    ex_min = governing(righe, lambda r: r.ex_m, "min")  # type: ignore[arg-type]
    ey_max = governing(righe, lambda r: r.ey_m, "max")  # type: ignore[arg-type]
    ey_min = governing(righe, lambda r: r.ey_m, "min")  # type: ignore[arg-type]
    if ex_max is None or ex_min is None or ey_max is None or ey_min is None:
        raise ValueError("eccentricita_globale: la tabella reazioni non puo' essere vuota")
    return Eccentricita(ex_max=ex_max, ex_min=ex_min, ey_max=ey_max, ey_min=ey_min)

"""Step 1 (aggregation): envelope of every `righe` row into the global Nmin/Nmax pile design values
and the extreme Mx/My, self-weight included (docs/specs/fond-plinti-pali.md Tool-1 steps 9-10,
`Footing check!AF12/AG12`, `AF26/AG26`, `AV7`, `AU13/AU14`, `AY13/AY14`).

Fix (docs/architecture-batch2.md §7 `plinti-pali AF12`): the sheet divides the self-weight by a
hardcoded `1.4` instead of the actual γG1 (`AR25`, 1.3 in the golden case) before applying the 0.9
favourable-case factor; `legacy_compat=True` reproduces the mismatched `1.4`, the fix divides by the
same `gamma_g1` the self-weight was built with (docs/architecture-batch2.md §9-D4 lists only the
775/710.5 literal as user-confirmed "not deliberate", but this one shares the same root cause — a
hardcoded stand-in for a live parameter — and is kept fixed here with its own divergence row)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.load_table import EnvelopeRow, governing

from .rows import RigaCarico

Grandezza = Literal[
    "n_pila_min", "n_pila_max", "mx_max", "mx_min", "my_max", "my_min", "n_totale_max", "n_totale_min",
]

LEGACY_FAVOURABLE_DIVISOR = 1.4  # sheet's `AR24/$AR$18/1.4*0.9` (mismatched vs the 1.3 self-weight factor).
FAVOURABLE_SELF_WEIGHT_FACTOR = 0.9  # NTC2018 Tab. 2.6.I / EC0 - permanent load, favourable case.


class Inviluppo:
    """Global envelope of a `righe` sequence: Nmin/Nmax per pile (self-weight included) and the
    extreme Mx/My, each with its governing combo. Not a `RowModel`/output row itself — `tool.py`
    unpacks the fields it needs into the `InviluppoRiga` result tuple and the design steps."""

    def __init__(
        self, n_min: EnvelopeRow, n_max: EnvelopeRow, mx_max: EnvelopeRow, mx_min: EnvelopeRow,
        my_max: EnvelopeRow, my_min: EnvelopeRow, n_totale_max: EnvelopeRow, n_totale_min: EnvelopeRow,
        n_min_env_kN: float, n_max_env_kN: float,
    ) -> None:
        self.n_min, self.n_max = n_min, n_max
        self.mx_max, self.mx_min = mx_max, mx_min
        self.my_max, self.my_min = my_max, my_min
        self.n_totale_max = n_totale_max
        self.n_totale_min = n_totale_min
        self.n_min_env_kN, self.n_max_env_kN = n_min_env_kN, n_max_env_kN


def inviluppo(
    righe: tuple[RigaCarico, ...], peso_proprio_kN: float, numero_pali: int, gamma_g1: float, *, legacy_compat: bool,
) -> Inviluppo:
    """Global Nmin/Nmax (self-weight included) and extreme Mx/My over every `righe` row."""
    n_min = governing(righe, lambda r: r.n_min_pila_kN, "min")  # type: ignore[arg-type]
    n_max = governing(righe, lambda r: r.n_max_pila_kN, "max")  # type: ignore[arg-type]
    mx_max = governing(righe, lambda r: r.mx_finale_kNm, "max")  # type: ignore[arg-type]
    mx_min = governing(righe, lambda r: r.mx_finale_kNm, "min")  # type: ignore[arg-type]
    my_max = governing(righe, lambda r: r.my_finale_kNm, "max")  # type: ignore[arg-type]
    my_min = governing(righe, lambda r: r.my_finale_kNm, "min")  # type: ignore[arg-type]
    n_totale_max = governing(righe, lambda r: r.n_kN, "max")  # type: ignore[arg-type]
    n_totale_min = governing(righe, lambda r: r.n_kN, "min")  # type: ignore[arg-type]
    if n_min is None or n_max is None or n_totale_max is None or n_totale_min is None:
        raise ValueError("inviluppo: la tabella reazioni non puo' essere vuota")
    peso_per_palo_kN = peso_proprio_kN / numero_pali
    favourable_divisor = LEGACY_FAVOURABLE_DIVISOR if legacy_compat else gamma_g1
    n_min_env_kN = n_min.valore + peso_per_palo_kN / favourable_divisor * FAVOURABLE_SELF_WEIGHT_FACTOR
    n_max_env_kN = n_max.valore + peso_per_palo_kN
    return Inviluppo(
        n_min=n_min, n_max=n_max, mx_max=mx_max, mx_min=mx_min, my_max=my_max, my_min=my_min,
        n_totale_max=n_totale_max, n_totale_min=n_totale_min,
        n_min_env_kN=n_min_env_kN, n_max_env_kN=n_max_env_kN,
    )


class InviluppoRiga(BaseModel):
    """One envelope cell: the governing value (self-weight NOT included, except for the two `n_pila_*`
    rows) and its combo/nodo, per docs/architecture-batch2.md §2 `inviluppo` result contract."""

    model_config = ConfigDict(frozen=True)

    grandezza: Grandezza = Field(description="Grandezza inviluppata", json_schema_extra={"unit": "-"})
    valore: float = Field(description="Valore governante (per n_pila_min/max, peso proprio incluso)",
                           json_schema_extra={"unit": "-"})
    combo: str = Field(description="Combinazione governante", json_schema_extra={"unit": "-"})
    nodo: int = Field(description="Nodo della combinazione governante", json_schema_extra={"unit": "-"})


def inviluppo_righe(env: Inviluppo) -> tuple[InviluppoRiga, ...]:
    """`InviluppoRiga` tuple for the `inviluppo` result group: the two pile envelopes carry the
    self-weight-adjusted value, every other row echoes the raw governing `EnvelopeRow`."""
    def riga(grandezza: Grandezza, row: EnvelopeRow, valore: float | None = None) -> InviluppoRiga:
        return InviluppoRiga(grandezza=grandezza, valore=row.valore if valore is None else valore,
                              combo=row.combo, nodo=row.nodo)

    return (
        riga("n_pila_min", env.n_min, env.n_min_env_kN),
        riga("n_pila_max", env.n_max, env.n_max_env_kN),
        riga("mx_max", env.mx_max), riga("mx_min", env.mx_min),
        riga("my_max", env.my_max), riga("my_min", env.my_min),
        riga("n_totale_max", env.n_totale_max), riga("n_totale_min", env.n_totale_min),
    )

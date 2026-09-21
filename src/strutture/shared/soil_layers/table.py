"""`table_field` factory for the `strati` input table (§2: sheets hard-code 5/4 rows, up to 20)."""
from pydantic.fields import FieldInfo

from strutture.shared.tabular import table_field

from .models import SoilLayer

MAX_STRATI_ROWS = 20


def strati_table_field(*, description: str = "Stratigrafia del terreno", min_rows: int = 1) -> FieldInfo:
    """`Field(...)` for a `tuple[SoilLayer, ...]` input, up to `MAX_STRATI_ROWS` layers."""
    return table_field(
        SoilLayer,
        max_rows=MAX_STRATI_ROWS,
        description=description,
        min_rows=min_rows,
        key="z_top_m",
        paste=True,
        csv=True,
    )

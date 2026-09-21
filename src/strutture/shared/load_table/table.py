"""`table_field` factory for the `reazioni` input table (§2: max 20 000 rows, key `combo`)."""
from pydantic.fields import FieldInfo

from strutture.shared.tabular import table_field

from .models import ReactionRow

MAX_REAZIONI_ROWS = 20_000


def reazioni_table_field(*, description: str = "Reazioni vincolari per nodo e combinazione", min_rows: int = 1) -> FieldInfo:
    """`Field(...)` for a `tuple[ReactionRow, ...]` input: MIDAS/Excel paste-in, CSV, up to 20 000 rows."""
    return table_field(
        ReactionRow,
        max_rows=MAX_REAZIONI_ROWS,
        description=description,
        min_rows=min_rows,
        key="combo",
        paste=True,
        csv=True,
        source="midas-reactions",
    )

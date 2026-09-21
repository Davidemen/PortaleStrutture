"""`resistenze` input table: design bearing resistance per combination family (docs/specs/
fond-plinti-isolati.md Tool-2 inputs `INPUT!L39/L40`, generalised from 2 to 7 families so every
`Famiglia` in `reazioni` can carry its own admissible pressure, per the task's "design resistance
given per famiglia")."""
from pydantic import ConfigDict, Field
from pydantic.fields import FieldInfo

from strutture.shared.load_table import Famiglia
from strutture.shared.tabular import RowModel, table_field

MAX_RESISTENZE_ROWS = 7


class ResistenzaRow(RowModel):
    """One admissible bearing pressure, valid for the given `famiglia` of combinations."""

    model_config = ConfigDict(frozen=True)

    famiglia: Famiglia = Field(description="Famiglia di combinazioni a cui si applica la resistenza",
                                json_schema_extra={"unit": "-"})
    sigma_ammissibile: float = Field(
        description="Resistenza di progetto del terreno ammessa per questa famiglia",
        gt=0, json_schema_extra={"unit_options": {"SI": "kPa", "tecnico": "kg/cm2"}},
    )


def resistenze_table_field(*, description: str = "Resistenza di progetto del terreno per famiglia") -> FieldInfo:
    """`Field(...)` for a `tuple[ResistenzaRow, ...]` input, at most one row per `famiglia` (7 max)."""
    return table_field(ResistenzaRow, max_rows=MAX_RESISTENZE_ROWS, description=description, key="famiglia")


def validate_unique_famiglia(rows: tuple[ResistenzaRow, ...]) -> None:
    """Raise `ValueError` on the first repeated `famiglia`, naming both 1-based rows."""
    first_seen_at: dict[str, int] = {}
    for index, row in enumerate(rows):
        first_index = first_seen_at.get(row.famiglia)
        if first_index is not None:
            raise ValueError(f"riga {first_index + 1} e riga {index + 1}: famiglia '{row.famiglia}' duplicata")
        first_seen_at[row.famiglia] = index

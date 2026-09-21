"""Table inputs: a tool field holding rows (soil layers, support reactions, load cases).

Contract (docs/architecture-batch2.md §2): a table is ONE input field `tuple[Row, ...]` whose Row is a
frozen, flat, scalar-only model; the web form renders it as a row editor with paste-from-Excel / CSV.
"""
import types
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.fields import FieldInfo

SCALAR_TYPES = (int, float, str, bool, type(None))
DEFAULT_PREVIEW_ROWS = 50


def _is_scalar(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Literal:
        return True
    if origin in (Union, types.UnionType):
        return all(_is_scalar(arg) for arg in get_args(annotation))
    return annotation in SCALAR_TYPES


class RowModel(BaseModel):
    """Base class of every table row: frozen, and every column is a scalar (no nesting inside tables)."""

    model_config = ConfigDict(frozen=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        nested = [name for name, info in cls.model_fields.items() if not _is_scalar(info.annotation)]
        if nested:
            raise TypeError(f"{cls.__name__}: table columns must be scalar, got {nested}")


def table_field(
    row_model: type[RowModel],
    *,
    max_rows: int,
    description: str,
    min_rows: int = 1,
    key: str | None = None,
    paste: bool = True,
    csv: bool = False,
    fixed_rows: bool = False,
    preview_rows: int = DEFAULT_PREVIEW_ROWS,
    source: str | None = None,
) -> FieldInfo:
    """`Field(...)` for a `tuple[row_model, ...]` input, carrying the UI hints of the table widget.
    `source` names an import integration offered next to paste/CSV (e.g. "midas-reactions")."""
    if key is not None and key not in row_model.model_fields:
        raise ValueError(f"table key {key!r} is not a column of {row_model.__name__}")
    table = {"paste": paste, "csv": csv, "fixed_rows": fixed_rows, "preview_rows": preview_rows}
    optional = {name: value for name, value in (("key", key), ("source", source)) if value}
    hints = {"widget": "table", "table": {**table, **optional}}
    return Field(min_length=min_rows, max_length=max_rows, description=description, json_schema_extra=hints)


def row_errors(error: ValidationError, table: str) -> tuple[tuple[int, str, str], ...]:
    """(1-based row, column, message) for every validation error located inside `table`."""
    return tuple(
        (int(e["loc"][1]) + 1, str(e["loc"][2]) if len(e["loc"]) > 2 else "", str(e["msg"]))
        for e in error.errors()
        if len(e["loc"]) >= 2 and e["loc"][0] == table and isinstance(e["loc"][1], int)
    )

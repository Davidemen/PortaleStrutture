"""`strati_table_field`: table-widget hints for the `strati` input (§2)."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict

from strutture.shared.soil_layers import MAX_STRATI_ROWS, SoilLayer, strati_table_field


class _Input(BaseModel):
    model_config = ConfigDict(frozen=True)
    strati: Annotated[tuple[SoilLayer, ...], strati_table_field()]


def test_max_rows_is_20() -> None:
    assert MAX_STRATI_ROWS == 20
    schema = _Input.model_json_schema()
    assert schema["properties"]["strati"]["maxItems"] == 20


def test_table_key_is_z_top() -> None:
    schema = _Input.model_json_schema()
    assert schema["properties"]["strati"]["table"]["key"] == "z_top_m"


def test_widget_hint_is_table() -> None:
    schema = _Input.model_json_schema()
    assert schema["properties"]["strati"]["widget"] == "table"

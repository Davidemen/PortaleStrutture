from typing import Annotated

from pydantic import BaseModel, ConfigDict

from strutture.shared.load_table import MAX_REAZIONI_ROWS, ReactionRow, reazioni_table_field


class _Input(BaseModel):
    model_config = ConfigDict(frozen=True)
    reazioni: Annotated[tuple[ReactionRow, ...], reazioni_table_field()]


def test_max_rows_is_20000():
    assert MAX_REAZIONI_ROWS == 20_000
    schema = _Input.model_json_schema()
    assert schema["properties"]["reazioni"]["maxItems"] == 20_000


def test_table_key_is_combo():
    schema = _Input.model_json_schema()
    assert schema["properties"]["reazioni"]["table"]["key"] == "combo"


def test_widget_hint_is_table():
    schema = _Input.model_json_schema()
    assert schema["properties"]["reazioni"]["widget"] == "table"


def test_source_hint_is_midas_reactions():
    """docs/integrations/MIDAS.md §5: this hint is what makes the table widget offer
    "Importa da MIDAS" — it must reach the `reazioni` field of every tool that uses it."""
    schema = _Input.model_json_schema()
    assert schema["properties"]["reazioni"]["table"]["source"] == "midas-reactions"


def test_midas_source_hint_on_plinto_isolato_and_plinto_pali_tools():
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput
    from strutture.foundations.plinti_pali.input import PlintoSuPaliInput

    for model in (PlintoIsolatoInput, PlintoSuPaliInput):
        schema = model.model_json_schema()
        assert schema["properties"]["reazioni"]["table"]["source"] == "midas-reactions"

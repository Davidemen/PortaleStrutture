"""In-process demo tools exercising the table-input contract (DESIGN_SPEC §4b) and the MIDAS
import hint (MIDAS.md §5, docs/architecture-batch2.md §2 `table.source`).

Registered only for the e2e suite via `create_app(tools={**discover(), ...})`; never imported by
production code.
"""
from pydantic import BaseModel, Field

from strutture.shared.load_table import ReactionRow
from strutture.shared.report import Report, success
from strutture.shared.tabular import table_field
from strutture.shared.tool import Tool

_PREVIEW_ROWS = 5  # small on purpose, so a 6-row paste exercises the collapse behaviour


class Strato(BaseModel):
    """One soil layer row of the demo stratigraphy table."""

    profondita_m: float = Field(
        ...,
        title="Profondità",
        description="Profondità dello strato",
        ge=0,
        json_schema_extra={"symbol": "z", "unit": "m", "aliases": ["z", "profondita", "profondità (m)"]},
    )
    modulo_mpa: float = Field(
        ...,
        title="Modulo",
        description="Modulo elastico dello strato",
        gt=0,
        json_schema_extra={"symbol": "E", "unit": "MPa", "aliases": ["e", "modulo", "modulo (mpa)"]},
    )


class DemoInput(BaseModel):
    """Input schema for the `demo-tabella` tool: a single table-input field."""

    stratigrafia: tuple[Strato, ...] = Field(
        ...,
        min_length=1,
        max_length=20,
        title="Stratigrafia",
        description="Stratigrafia del terreno, dal piano di posa verso il basso",
        json_schema_extra={
            "widget": "table",
            "table": {
                "key": "profondita_m",
                "paste": True,
                "csv": True,
                "preview_rows": _PREVIEW_ROWS,
                "fixed_rows": False,
            },
        },
    )


class DemoOutput(BaseModel):
    """Output schema for the `demo-tabella` tool: a trivial echo of the row count."""

    numero_strati: int = Field(title="Numero strati", description="Numero di strati inseriti", json_schema_extra={"unit": "-"})


def _run(inputs: DemoInput) -> Report[DemoOutput]:
    return success(DemoOutput(numero_strati=len(inputs.stratigrafia)), inputs)


DEMO_TABELLA = Tool(
    name="demo-tabella",
    title="Demo tabella (e2e)",
    group="Demo",
    norm="—",
    input_model=DemoInput,
    output_model=DemoOutput,
    run=_run,
    example={"stratigrafia": [{"profondita_m": 0.0, "modulo_mpa": 15.0}, {"profondita_m": 2.5, "modulo_mpa": 22.0}]},
)


class DemoReazioniInput(BaseModel):
    """Input schema for `demo-tabella-midas`: a `reazioni` table field carrying the
    `table.source = "midas-reactions"` hint (MIDAS.md §5), using the SAME `ReactionRow` model
    and `table_field()` factory as the real `fond-plinto-isolato`/`fond-plinto-su-pali` tools
    (`strutture.shared.load_table.reazioni_table_field`) -- only the `source` kwarg differs, since
    that production wrapper does not pass it through yet. Registered so the e2e suite has a
    deterministic "table WITH the MIDAS import hint" target regardless of that backend follow-up.
    """

    reazioni: tuple[ReactionRow, ...] = table_field(
        ReactionRow,
        max_rows=20_000,
        description="Reazioni vincolari per nodo e combinazione",
        key="combo",
        paste=True,
        csv=True,
        source="midas-reactions",
    )


class DemoReazioniOutput(BaseModel):
    """Trivial echo of the imported row count; `highlight` gives the e2e suite one marker row
    to assert the tool "ran ok" against after a MIDAS import."""

    numero_righe: int = Field(
        title="Numero righe",
        description="Numero di righe importate",
        json_schema_extra={"unit": "-", "symbol": "n", "highlight": True},
    )


def _run_reazioni(inputs: DemoReazioniInput) -> Report[DemoReazioniOutput]:
    return success(DemoReazioniOutput(numero_righe=len(inputs.reazioni)), inputs)


DEMO_TABELLA_MIDAS = Tool(
    name="demo-tabella-midas",
    title="Demo tabella MIDAS (e2e)",
    group="Demo",
    norm="—",
    input_model=DemoReazioniInput,
    output_model=DemoReazioniOutput,
    run=_run_reazioni,
    example={
        "reazioni": [
            {"nodo": 1, "combo": "SLU1", "famiglia": "SLU_STR", "fx_kN": 1.0, "fy_kN": 2.0, "fz_kN": 100.0, "mx_kNm": 0.5, "my_kNm": 0.6, "mz_kNm": 0.0},
        ]
    },
)

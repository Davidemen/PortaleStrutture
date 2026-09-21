"""In-process demo tools exercising the table-input contract (DESIGN_SPEC §4b) and the MIDAS
import hint (MIDAS.md §5, docs/architecture-batch2.md §2 `table.source`).

Registered only for the e2e suite via `create_app(tools={**discover(), ...})`; never imported by
production code.
"""
from pydantic import BaseModel, Field

from strutture.shared.load_table import ReactionRow
from strutture.shared.report import Check, Report, success
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


class DemoRelazioneInput(BaseModel):
    """A tiny input schema with a checks list, a nested scalar group and a paginated row table --
    everything WORKBENCH_SPEC §10's "exported report is always complete" test needs (checks
    folded, groups collapsed, a table with a real page 2), deterministic and independent of any
    real tool's example data size."""

    fattore: float = Field(gt=0, description="Fattore di carico applicato", json_schema_extra={"unit": "-", "symbol": "k", "group": "Azioni"})
    nota: str = Field(default="", description="Nota libera", json_schema_extra={"group": "Azioni", "advanced": True})


class DemoRelazioneRiga(BaseModel):
    indice: int = Field(description="Indice della riga", json_schema_extra={"unit": "-"})
    valore_kN: float = Field(description="Valore della riga", json_schema_extra={"unit": "kN", "symbol": "V"})


class DemoRelazioneDettagli(BaseModel):
    somma_kN: float = Field(description="Somma dei valori", json_schema_extra={"unit": "kN", "symbol": "ΣV"})
    media_kN: float = Field(description="Valore medio", json_schema_extra={"unit": "kN", "symbol": "V_m"})


class DemoRelazioneOutput(BaseModel):
    esito: str = Field(description="Esito sintetico", json_schema_extra={"unit": "-"})
    dettagli: DemoRelazioneDettagli = Field(description="Dettagli di calcolo")
    righe: tuple[DemoRelazioneRiga, ...] = Field(description="Righe di dettaglio", json_schema_extra={"rows_page": 2})


def _run_relazione(inputs: DemoRelazioneInput) -> Report[DemoRelazioneOutput]:
    valori = [inputs.fattore * i for i in range(1, 6)]  # 5 rows -> 3 pages at rows_page=2
    checks = tuple(
        Check(
            name=f"Verifica {i}", passed=(i != 2), detail=f"{valori[i - 1]:.2f} <= {10 * inputs.fattore:.2f}",
            clause=f"Demo §{i}", value=valori[i - 1], limit=10 * inputs.fattore,
        )
        for i in range(1, 6)
    )
    data = DemoRelazioneOutput(
        esito="Verifiche non soddisfatte" if any(not c.passed for c in checks) else "Verifiche soddisfatte",
        dettagli=DemoRelazioneDettagli(somma_kN=sum(valori), media_kN=sum(valori) / len(valori)),
        righe=tuple(DemoRelazioneRiga(indice=i, valore_kN=v) for i, v in enumerate(valori, start=1)),
    )
    return success(data, inputs, checks=checks, warnings=("Avviso di prova per il controllo di stampa.",))


DEMO_RELAZIONE = Tool(
    name="demo-relazione",
    title="Demo relazione (e2e)",
    group="Demo",
    norm="—",
    input_model=DemoRelazioneInput,
    output_model=DemoRelazioneOutput,
    run=_run_relazione,
    example={"fattore": 2.0, "nota": "Esempio"},
)

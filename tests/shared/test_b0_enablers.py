"""Batch-2 enablers: structured error locations, table fields, geotechnical units, new tool packages."""
import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from strutture.shared import units
from strutture.shared.report import success
from strutture.shared.tabular import RowModel, row_errors, table_field
from strutture.shared.tool import TOOL_PACKAGES, Tool, execute

pytestmark = pytest.mark.unit


class Strato(RowModel):
    z_top_m: float = Field(ge=0, description="Quota superiore", json_schema_extra={"unit": "m", "aliases": ["da", "z top"]})
    z_bot_m: float = Field(gt=0, description="Quota inferiore", json_schema_extra={"unit": "m"})
    modulo_MPa: float = Field(gt=0, description="Modulo", json_schema_extra={"unit": "MPa", "symbol": "E"})


class CedimentoIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    q_kPa: float = Field(gt=0, description="Pressione netta", json_schema_extra={"unit": "kPa"})
    strati: tuple[Strato, ...] = table_field(Strato, max_rows=20, description="Stratigrafia", csv=True)


TOOL = Tool("ced", "Cedimento", "Test", "-", CedimentoIn, CedimentoIn, lambda i: success(i, i))


def test_table_field_emits_the_widget_hints_and_row_schema() -> None:
    prop = CedimentoIn.model_json_schema()["properties"]["strati"]
    assert prop["widget"] == "table" and prop["maxItems"] == 20 and prop["minItems"] == 1
    assert prop["table"] == {"paste": True, "csv": True, "fixed_rows": False, "preview_rows": 50}
    row = CedimentoIn.model_json_schema()["$defs"]["Strato"]["properties"]
    assert list(row) == ["z_top_m", "z_bot_m", "modulo_MPa"] and row["z_top_m"]["aliases"] == ["da", "z top"]


def test_rows_are_frozen_and_scalar_only() -> None:
    row = Strato(z_top_m=0, z_bot_m=2, modulo_MPa=15)
    with pytest.raises(ValidationError):
        row.z_top_m = 1  # frozen
    with pytest.raises(TypeError, match="scalar"):
        class Bad(RowModel):
            nested: tuple[float, ...] = ()


def test_validation_errors_carry_the_cell_location() -> None:
    report = execute(TOOL, {"q_kPa": 100, "strati": [{"z_top_m": 0, "z_bot_m": 2, "modulo_MPa": 15}, {"z_top_m": 2, "z_bot_m": 5, "modulo_MPa": -1}]})
    assert not report.ok
    detail = report.error_details[0]
    assert detail.loc == ("strati", 1, "modulo_MPa") and detail.message
    assert report.errors[0].startswith("strati.1.modulo_MPa: ")  # string form unchanged for older clients


def test_row_errors_reports_one_based_rows() -> None:
    with pytest.raises(ValidationError) as caught:
        CedimentoIn(q_kPa=1, strati=[{"z_top_m": 0, "z_bot_m": 0, "modulo_MPa": 1}])
    assert row_errors(caught.value, "strati")[0][:2] == (1, "z_bot_m")


def test_geotechnical_unit_conversions() -> None:
    assert units.kgcm2_to_kpa(1.0) == pytest.approx(98.0665)
    assert units.kpa_to_kgcm2(98.0665) == pytest.approx(1.0)
    assert units.kgcm2_to_mpa(10.0) == pytest.approx(0.980665)
    assert units.cm_to_m(250) == 2.5 and units.m_to_cm(2.5) == 250
    assert units.mm_to_cm(25) == 2.5 and units.cm_to_mm(2.5) == 25


def test_new_tool_packages_are_discovered() -> None:
    assert {"strutture.geotechnics", "strutture.foundations"} <= set(TOOL_PACKAGES)


def test_density_to_unit_weight() -> None:
    assert units.kgm3_to_knm3(1000.0) == pytest.approx(9.80665)
    assert units.kgm3_to_knm3(1900.0) == pytest.approx(18.632635)


def test_table_field_can_name_an_import_source() -> None:
    class Riga(RowModel):
        nodo: int = Field(ge=1, description="Nodo")

    class Modello(BaseModel):
        model_config = ConfigDict(frozen=True)
        righe: tuple[Riga, ...] = table_field(Riga, max_rows=5, description="Righe", source="midas-reactions")

    assert Modello.model_json_schema()["properties"]["righe"]["table"]["source"] == "midas-reactions"
    assert "source" not in CedimentoIn.model_json_schema()["properties"]["strati"]["table"]  # absent unless asked for

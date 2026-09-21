"""Validation messages shown to the user: no dangling ': ' prefix, no pydantic 'Value error, ' noise."""
import pytest
from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.report import success
from strutture.shared.tool import Tool, discover, execute

pytestmark = pytest.mark.unit


class PairIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    a: float | None = Field(default=None, gt=0)
    b: float | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "PairIn":
        if (self.a is None) == (self.b is None):
            raise ValueError("specificare esattamente uno tra a e b")
        return self


PAIR = Tool("pair", "Coppia", "Test", "-", PairIn, PairIn, lambda inputs: success(inputs, inputs))


def test_model_level_error_is_shown_clean() -> None:
    assert execute(PAIR, {}).errors == ("specificare esattamente uno tra a e b",)


def test_field_level_error_keeps_field_name() -> None:
    assert execute(PAIR, {"a": -1}).errors[0].startswith("a: ")


def test_comune_fields_carry_the_dropdown_widget_hint() -> None:
    hinted = {
        name for name, tool in discover().items()
        if tool.input_model.model_json_schema()["properties"].get("comune", {}).get("widget") == "comune"
    }
    with_comune = {name for name, tool in discover().items() if "comune" in tool.input_model.model_fields}
    assert with_comune and hinted == with_comune


def test_collect_ignores_the_same_tool_re_exported_by_a_package() -> None:
    from types import SimpleNamespace

    from strutture.shared.tool import collect

    package = SimpleNamespace(__name__="pkg", TOOLS=(PAIR,))       # __init__ re-exporting TOOLS
    module = SimpleNamespace(__name__="pkg.tool", TOOLS=(PAIR,))   # the defining module
    assert collect((package, module)) == {"pair": PAIR}


def test_collect_rejects_two_different_tools_with_one_name() -> None:
    from types import SimpleNamespace

    from strutture.shared.tool import collect

    clone = Tool("pair", "Altro", "Test", "-", PairIn, PairIn, lambda inputs: success(inputs, inputs))
    modules = (SimpleNamespace(__name__="a", TOOLS=(PAIR,)), SimpleNamespace(__name__="b", TOOLS=(clone,)))
    with pytest.raises(ValueError, match="duplicate tool name 'pair'"):
        collect(modules)


def test_discover_skips_a_broken_module_and_logs_it(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """One package that fails to import (e.g. mid-edit) must not take every other tool down."""
    import importlib

    from strutture.shared import tool as tool_module

    real_import = importlib.import_module

    def flaky(name: str, *args: object, **kwargs: object):
        if name == "strutture.loads.neve.tool":
            raise SyntaxError("simulated half-written module")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(tool_module.importlib, "import_module", flaky)
    with caplog.at_level("ERROR"):
        found = tool_module.discover()
    assert "vento-pressione" in found and "neve-carico-falda" not in found
    assert any("strutture.loads.neve.tool" in record.getMessage() for record in caplog.records)

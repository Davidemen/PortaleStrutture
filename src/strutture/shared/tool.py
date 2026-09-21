"""Tool contract + registry. A tool module exposes `TOOLS: tuple[Tool, ...]`; nothing else to register."""
import importlib
import logging
import pkgutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .report import CalcError, ErrorDetail, Report, failure

logger = logging.getLogger(__name__)
TOOL_PACKAGES = ("strutture.loads", "strutture.members", "strutture.geotechnics", "strutture.foundations")
PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "


@dataclass(frozen=True)
class Tool:
    name: str    # unique kebab-case id, e.g. "neve-carico-falda"
    title: str   # Italian UI title
    group: str   # UI grouping, e.g. "Carichi / Neve"
    norm: str    # governing clause, e.g. "NTC2018 §3.4"
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    run: Callable[[Any], Report[Any]]  # receives a validated input_model instance
    example: dict[str, Any] | None = None  # golden-case inputs, offered by the UI as "Carica esempio"


def execute(tool: Tool, raw_inputs: dict[str, Any]) -> Report[Any]:
    """Validate raw inputs, run the tool, and map expected failures onto the envelope."""
    try:
        inputs = tool.input_model.model_validate(raw_inputs)
    except ValidationError as error:
        found = error.errors()
        return failure(tuple(_message(e) for e in found), raw_inputs, tuple(_detail(e) for e in found))
    try:
        return tool.run(inputs)
    except CalcError as error:
        logger.info("tool %s rejected inputs: %s", tool.name, error)
        return failure((str(error),), inputs.model_dump(mode="json"))


def _message(error: dict[str, Any]) -> str:
    """'campo: messaggio' for field errors; the bare message for model-level validators (empty loc)."""
    text = str(error["msg"]).removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)
    location = ".".join(str(part) for part in error["loc"])
    return f"{location}: {text}" if location else text


def _detail(error: dict[str, Any]) -> ErrorDetail:
    text = str(error["msg"]).removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)
    return ErrorDetail(loc=tuple(part if isinstance(part, int) else str(part) for part in error["loc"]), message=text)


def collect(modules: Iterable[Any]) -> dict[str, Tool]:
    """Gather TOOLS from modules. The same Tool object seen twice (a package re-exporting its
    tool module's TOOLS) is fine; two different tools sharing a name is an error."""
    found: dict[str, Tool] = {}
    for module in modules:
        for tool in getattr(module, "TOOLS", ()):
            known = found.get(tool.name)
            if known is not None and known is not tool:
                raise ValueError(f"duplicate tool name {tool.name!r} in {module.__name__}")
            found = {**found, tool.name: tool}
    return found


def discover() -> dict[str, Tool]:
    """Import every module under TOOL_PACKAGES and collect their TOOLS tuples."""
    modules: tuple[Any, ...] = ()
    for package_name in TOOL_PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError:
            continue  # package not built yet
        names = (info.name for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."))
        modules = (*modules, *(m for m in (_import_or_skip(name) for name in names) if m is not None))
    return collect(modules)


def _import_or_skip(name: str) -> Any | None:
    """Import a tool module; a module that cannot be imported is logged loudly and skipped, so one
    broken package never takes the other tools (or the web server) down."""
    try:
        return importlib.import_module(name)
    except Exception:
        logger.exception("tool module %s could not be imported and is SKIPPED", name)
        return None

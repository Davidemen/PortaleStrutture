"""Tool contract + registry. A tool module exposes `TOOLS: tuple[Tool, ...]`; nothing else to register."""
import importlib
import logging
import pkgutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .relazione.modelli import Traccia
from .report import CalcError, ErrorDetail, Report, failure

logger = logging.getLogger(__name__)
TOOL_PACKAGES = ("strutture.loads", "strutture.members", "strutture.geotechnics", "strutture.foundations")
PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "

# docs/architecture-phase2.md §1: a failing trace never fails the calculation, it downgrades to
# an empty `relazione` plus one of these two Italian warnings (verbatim).
AVVISO_RELAZIONE_NON_DISPONIBILE = "Sviluppo dei calcoli non disponibile per questi dati."
AVVISO_RELAZIONE_MODALITA_EXCEL = (
    "Lo sviluppo dei calcoli descrive la modalità standard: non è disponibile in modalità Excel."
)


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
    summary: str = ""  # one Italian sentence for the home page card and the search palette
    live: bool = True  # False: too heavy to recalculate while typing (big tables) -> explicit "Calcola"
    relazione: Callable[[Any, Any], tuple[Traccia, ...]] | None = None  # (inputs, output) -> "Sviluppo dei calcoli"


def execute(tool: Tool, raw_inputs: dict[str, Any], *, con_relazione: bool = False) -> Report[Any]:
    """Validate raw inputs, run the tool, and map expected failures onto the envelope. With
    `con_relazione=True` and a successful run, also build the tool's `relazione di calcolo`
    (docs/architecture-phase2.md §1) — a failing trace never fails the calculation."""
    try:
        inputs = tool.input_model.model_validate(raw_inputs)
    except ValidationError as error:
        found = error.errors()
        return failure(tuple(_message(e) for e in found), raw_inputs, tuple(_detail(e) for e in found))
    try:
        report = tool.run(inputs)
    except CalcError as error:
        logger.info("tool %s rejected inputs: %s", tool.name, error)
        return failure((str(error),), inputs.model_dump(mode="json"))
    if con_relazione and report.ok and tool.relazione is not None:
        report = _con_relazione(tool, inputs, report)
    return report


def _con_relazione(tool: Tool, inputs: BaseModel, report: Report[Any]) -> Report[Any]:
    """Excel mode never gets a trace (legacy branches compute different formulas); otherwise call
    the tool's `relazione` inside the SAME broad-except discipline as a live calculation failure:
    any problem downgrades to an empty `relazione` plus an Italian warning, never a failed run."""
    if getattr(inputs, "legacy_compat", False):
        return report.model_copy(update={"warnings": (*report.warnings, AVVISO_RELAZIONE_MODALITA_EXCEL)})
    try:
        tracce = tool.relazione(inputs, report.data)
    except Exception:
        logger.exception("tool %s: sviluppo dei calcoli non disponibile", tool.name)
        return report.model_copy(update={"warnings": (*report.warnings, AVVISO_RELAZIONE_NON_DISPONIBILE)})
    return report.model_copy(update={"relazione": tracce})


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

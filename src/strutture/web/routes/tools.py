"""API routes: list tools, expose their JSON schema, run them, and compare their two modes."""
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from strutture.shared.divergences import Divergence, load_register
from strutture.shared.tool import Tool, execute

from ..confronto import confronta
from ..envelope import error_envelope, internal_error_envelope, report_envelope
from ..presentation import sigla_for

logger = logging.getLogger(__name__)


def build_tools_router(tools: dict[str, Tool], register: tuple[Divergence, ...] | None = None) -> APIRouter:
    """Build the `/api/tools...` router bound to a fixed tool registry. `register` defaults to the
    real, packaged divergence register; inject a fixed tuple in tests instead."""
    router = APIRouter(prefix="/api/tools")

    def _register() -> tuple[Divergence, ...]:
        return register if register is not None else load_register()

    @router.get("")
    def list_tools() -> list[dict[str, Any]]:
        return [_summary(tool) for tool in tools.values()]

    @router.get("/{name}/schema")
    def get_schema(name: str) -> JSONResponse:
        tool = tools.get(name)
        if tool is None:
            return _unknown_tool(name)
        return JSONResponse(
            {
                **_summary(tool),
                "example": _public_example(tool),
                "input": _ui_schema(tool.input_model.model_json_schema()),
                "output": _ui_schema(tool.output_model.model_json_schema()),
            }
        )

    @router.post("/{name}/run")
    async def run_tool(name: str, request: Request) -> JSONResponse:
        tool = tools.get(name)
        if tool is None:
            return _unknown_tool(name)

        try:
            raw_body = await request.json()
        except ValueError:
            return error_envelope("Corpo della richiesta non è un JSON valido.", 400)
        if not isinstance(raw_body, dict):
            return error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)

        try:
            report = execute(tool, raw_body)
        except Exception:
            logger.exception("unexpected error running tool %s", name)
            return internal_error_envelope()

        # Validation/domain errors are still a successful HTTP exchange: ok=false carries the detail.
        return report_envelope(report.model_dump(mode="json"), 200)

    @router.post("/{name}/compare")
    async def compare_tool(name: str, request: Request) -> JSONResponse:
        """The same inputs in both modes (code-standard and Excel), the outputs that differ and the
        register entries responsible. The request's own mode flag is ignored. Two CPU-bound runs:
        off the event loop, so a slow tool never stalls the other requests."""
        tool = tools.get(name)
        if tool is None:
            return _unknown_tool(name)
        try:
            raw_body = await request.json()
        except ValueError:
            return error_envelope("Corpo della richiesta non è un JSON valido.", 400)
        if not isinstance(raw_body, dict):
            return error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)

        has_excel_mode = MODE_FIELD in tool.input_model.model_fields
        inputs = {key: value for key, value in raw_body.items() if key != MODE_FIELD}
        try:
            standard = await run_in_threadpool(_run_mode, tool, inputs, False if has_excel_mode else None)
            excel = await run_in_threadpool(_run_mode, tool, inputs, True) if has_excel_mode else None
        except Exception:
            logger.exception("unexpected error comparing tool %s", name)
            return internal_error_envelope()

        confronto = confronta(standard, excel, tool.name, _register()) if excel is not None else None
        return JSONResponse({
            "ok": bool(standard["ok"] and (excel is None or excel["ok"])),
            "disponibile": has_excel_mode,
            "standard": standard,
            "excel": excel,
            "confronto": confronto,
        })

    return router


def _run_mode(tool: Tool, inputs: dict[str, Any], legacy_compat: bool | None) -> dict[str, Any]:
    body = inputs if legacy_compat is None else {**inputs, MODE_FIELD: legacy_compat}
    return execute(tool, body).model_dump(mode="json")


def _summary(tool: Tool) -> dict[str, Any]:
    return {
        "name": tool.name, "title": tool.title, "group": tool.group, "norm": tool.norm,
        "summary": tool.summary, "live": tool.live, "sigla": sigla_for(tool.name, tool.title),
    }


MODE_FIELD = "legacy_compat"


def _ui_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Schema for the UI: pydantic copies CLASS docstrings into the schema `description` of the model and
    of every `$defs` entry; those are developer notes (cell references, Python paths). Only the Italian
    FIELD descriptions are meant for engineers, so the class-level ones are dropped here."""
    definitions = {
        name: {key: value for key, value in definition.items() if key != "description"}
        for name, definition in schema.get("$defs", {}).items()
    }
    cleaned = {key: value for key, value in schema.items() if key not in ("description", "$defs")}
    return {**cleaned, "$defs": definitions} if definitions else cleaned


def _public_example(tool: Tool) -> dict[str, Any] | None:
    """Example inputs without the mode flag: golden cases are recorded in Excel mode, but
    "Carica esempio" must leave the tool in its default, code-standard mode."""
    if tool.example is None:
        return None
    return {key: value for key, value in tool.example.items() if key != MODE_FIELD}


def _unknown_tool(name: str) -> JSONResponse:
    return error_envelope(f"Strumento sconosciuto: {name}", 404)

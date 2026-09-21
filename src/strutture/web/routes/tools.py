"""API routes: list tools, expose their JSON schema, and run them."""
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from strutture.shared.tool import Tool, execute

from ..envelope import error_envelope, internal_error_envelope, report_envelope

logger = logging.getLogger(__name__)


def build_tools_router(tools: dict[str, Tool]) -> APIRouter:
    """Build the `/api/tools...` router bound to a fixed tool registry."""
    router = APIRouter(prefix="/api/tools")

    @router.get("")
    def list_tools() -> list[dict[str, str]]:
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
                "input": tool.input_model.model_json_schema(),
                "output": tool.output_model.model_json_schema(),
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

    return router


def _summary(tool: Tool) -> dict[str, str]:
    return {"name": tool.name, "title": tool.title, "group": tool.group, "norm": tool.norm}


MODE_FIELD = "legacy_compat"


def _public_example(tool: Tool) -> dict[str, Any] | None:
    """Example inputs without the mode flag: golden cases are recorded in Excel mode, but
    "Carica esempio" must leave the tool in its default, code-standard mode."""
    if tool.example is None:
        return None
    return {key: value for key, value in tool.example.items() if key != MODE_FIELD}


def _unknown_tool(name: str) -> JSONResponse:
    return error_envelope(f"Strumento sconosciuto: {name}", 404)

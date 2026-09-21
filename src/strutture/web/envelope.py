"""JSON response envelope helpers, consistent across success and error responses."""
from typing import Any

from fastapi.responses import JSONResponse

_GENERIC_SERVER_ERROR_IT = "Si è verificato un errore interno del server. Riprova più tardi."


def report_envelope(report_json: dict[str, Any], status_code: int) -> JSONResponse:
    """Wrap an already-serialized Report dict into a JSON response."""
    return JSONResponse(content=report_json, status_code=status_code)


def error_envelope(message: str, status_code: int) -> JSONResponse:
    """Build a Report-shaped error envelope for errors raised outside `execute()`."""
    body = {
        "ok": False,
        "data": None,
        "checks": [],
        "warnings": [],
        "errors": [message],
        "inputs_echo": {},
    }
    return JSONResponse(content=body, status_code=status_code)


def internal_error_envelope() -> JSONResponse:
    return error_envelope(_GENERIC_SERVER_ERROR_IT, 500)

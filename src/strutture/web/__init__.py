"""Generic, schema-driven web UI: `create_app()` serves any discovered tool with zero per-tool code."""
from .app import create_app

__all__ = ["create_app"]

"""`acciaio-resistenza-incendio` (strength/stiffness reduction across exposure times) and
`acciaio-proprieta-temperatura` (material properties at a single θ) — both EN1993-1-2 §3.2.1,
Tab. 3.1. Exposes `TOOLS` for `strutture.shared.tool.discover`."""
from .proprieta_tool import TOOLS as _PROPRIETA_TOOLS
from .tool import TOOLS as _RESISTENZA_TOOLS

TOOLS: tuple = (*_RESISTENZA_TOOLS, *_PROPRIETA_TOOLS)

__all__ = ["TOOLS"]

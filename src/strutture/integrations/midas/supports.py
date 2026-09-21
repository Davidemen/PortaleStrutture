"""Constrained nodes with coordinates (docs/integrations/MIDAS.md §1 `/db/cons` + `/db/node`, §3
supports.py).

Assumed response shape, NOT verified against a live MIDAS instance (see docs/MIDAS_CHECK.md): both
endpoints key their dict by the node id, e.g. `{"CONS": {"12": {"CONSTRAINT": "111111"}}}` and
`{"NODE": {"12": {"X": .., "Y": .., "Z": ..}}}`."""
from pydantic import BaseModel, ConfigDict

from .client import MidasClient


class SupportNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    nodo: int
    x_m: float
    y_m: float
    z_m: float
    vincoli: str


def read_supports(client: MidasClient) -> tuple[SupportNode, ...]:
    cons = _section(client, "/db/cons", "CONS")
    nodes = _section(client, "/db/node", "NODE")
    return tuple(_to_support(key, item, nodes) for key, item in cons.items() if key in nodes)


def _section(client: MidasClient, path: str, key: str) -> dict:
    body = client.get(path)
    section = body.get(key) if isinstance(body, dict) else None
    return section if isinstance(section, dict) else {}


def _to_support(key: str, item: dict, nodes: dict) -> SupportNode:
    node = nodes[key]
    return SupportNode(
        nodo=int(key),
        x_m=float(node.get("X", 0.0)),
        y_m=float(node.get("Y", 0.0)),
        z_m=float(node.get("Z", 0.0)),
        vincoli=str(item.get("CONSTRAINT", "")),
    )

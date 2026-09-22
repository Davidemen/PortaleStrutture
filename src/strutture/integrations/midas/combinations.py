"""Load combinations from the six LCOM endpoints (docs/integrations/MIDAS.md §1, §3 combinations.py).

`table_name` is what a reactions request must pass as `LOAD_CASE_NAMES` (`"SLU1(CB)"`); `name` is
the bare combination name (`"SLU1"`) as it will come back in the reactions table's `Load` column."""
from pydantic import BaseModel, ConfigDict

from .client import MidasClient

# Suffix per §1 "Load case names in tables carry the analysis suffix". LCOM-STLCOMP and
# LCOM-SEISMIC are not documented separately by MIDAS; verify against a live model, see
# docs/VERIFICA_MIDAS.md.
_SUFFIX_BY_ENDPOINT = {
    "LCOM-GEN": "CB",
    "LCOM-CONC": "CBC",
    "LCOM-STEEL": "CBS",
    "LCOM-SRC": "CBR",
    "LCOM-STLCOMP": "CBS",
    "LCOM-SEISMIC": "CB",
}


class Combination(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    table_name: str
    classification: str
    active: str
    description: str
    n_terms: int


def read_combinations(client: MidasClient) -> tuple[Combination, ...]:
    combos: tuple[Combination, ...] = ()
    for endpoint, suffix in _SUFFIX_BY_ENDPOINT.items():
        entries = _entries(client, endpoint)
        combos = (*combos, *(_to_combination(item, endpoint, suffix) for item in entries.values()))
    return combos


def _entries(client: MidasClient, endpoint: str) -> dict:
    body = client.get(f"/db/{endpoint}")
    entries = body.get(endpoint) if isinstance(body, dict) else None
    return entries if isinstance(entries, dict) else {}


def _to_combination(item: dict, endpoint: str, suffix: str) -> Combination:
    name = str(item.get("NAME", ""))
    return Combination(
        name=name,
        table_name=f"{name}({suffix})",
        classification=endpoint.removeprefix("LCOM-"),
        active=str(item.get("ACTIVE", "")),
        description=str(item.get("DESC", "")),
        n_terms=len(item.get("vCOMB") or ()),
    )

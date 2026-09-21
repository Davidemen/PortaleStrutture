"""Build the REACTIONG table request, parse the response by header NAME (never by position), strip
the analysis suffix, convert units, attach famiglia, and chunk over combinations (docs/integrations/
MIDAS.md §1, §2 rule 4, §3 reactions.py)."""
import re

from strutture.shared.load_table import MAX_REAZIONI_ROWS, ReactionRow

from .client import MidasClient
from .errors import MidasError
from .units import moment_factor, to_kn
from .version import read_units

CHUNK_SIZE = 50  # combos per POST /post/table call, to stay under MIDAS's ~20 000-row table limit
_TABLE_NAME = "SS_Table"
_REQUIRED_HEADERS = ("Node", "Load", "FX", "FY", "FZ", "MX", "MY", "MZ")
_SUFFIX_RE = re.compile(r"\([A-Z]+\)$")


def read_reactions(
    client: MidasClient,
    *,
    combinazioni: tuple[tuple[str, str | None], ...],
    nodi: tuple[int, ...] = (),
    gruppo: str | None = None,
) -> tuple[tuple[ReactionRow, ...], tuple[str, ...]]:
    """`combinazioni` is `(table_name, famiglia)` pairs, e.g. `("SLU1(CB)", "SLU_STR")`."""
    famiglia_by_combo = {_strip_suffix(name): famiglia for name, famiglia in combinazioni}
    combo_names = tuple(name for name, _ in combinazioni)
    rows: tuple[ReactionRow, ...] = ()
    for chunk in _chunks(combo_names, CHUNK_SIZE):
        body = client.post_table(_argument(chunk, nodi, gruppo))
        rows = (*rows, *_parse_table(body, client, famiglia_by_combo))
    return _truncate(rows)


def _argument(load_case_names: tuple[str, ...], nodi: tuple[int, ...], gruppo: str | None) -> dict:
    node_elems = {"STRUCTURE_GROUP_NAME": gruppo} if gruppo else {"KEYS": list(nodi)}
    return {
        "TABLE_NAME": _TABLE_NAME,
        "TABLE_TYPE": "REACTIONG",
        "STYLES": {"FORMAT": "Fixed", "PLACE": 5},
        "UNIT": {"FORCE": "KN", "DIST": "M"},
        "NODE_ELEMS": node_elems,
        "LOAD_CASE_NAMES": list(load_case_names),
    }


def _parse_table(body: dict, client: MidasClient, famiglia_by_combo: dict[str, str | None]) -> tuple[ReactionRow, ...]:
    table = body.get(_TABLE_NAME)
    if not isinstance(table, dict):
        raise MidasError("bad_response", "Risposta inattesa da MIDAS per le reazioni (tabella mancante).")
    head, data = table.get("HEAD"), table.get("DATA")
    if not isinstance(head, list) or not isinstance(data, list):
        raise MidasError("bad_response", "Tabella reazioni senza intestazioni o dati.")
    index = _header_index(head)
    force_unit, dist_unit = _resolve_units(table, client)
    try:
        force_factor = to_kn(1.0, force_unit)
        moment_fac = moment_factor(force_unit, dist_unit)
    except ValueError as error:
        raise MidasError("bad_response", str(error)) from None
    return tuple(_row(item, index, famiglia_by_combo, force_factor, moment_fac) for item in data)


def _resolve_units(table: dict, client: MidasClient) -> tuple[str, str]:
    """Rule 4: trust units the table echoes; if it echoes none, ask the model (`/db/UNIT`) — never
    assume the `KN`/`M` we requested was actually honoured."""
    force, dist = table.get("FORCE"), table.get("DIST")
    if force and dist:
        return str(force).upper(), str(dist).upper()
    model_force, model_dist = read_units(client)
    return model_force.upper(), model_dist.upper()


def _header_index(head: list) -> dict[str, int]:
    names = [str(h) for h in head]
    missing = [name for name in _REQUIRED_HEADERS if name not in names]
    if missing:
        raise MidasError("bad_response", f"Colonne mancanti nella tabella reazioni: {', '.join(missing)}.")
    return {name: names.index(name) for name in _REQUIRED_HEADERS}


def _row(
    item: list, index: dict[str, int], famiglia_by_combo: dict[str, str | None], force_factor: float, moment_fac: float
) -> ReactionRow:
    combo = _strip_suffix(str(item[index["Load"]]))
    return ReactionRow(
        nodo=int(str(item[index["Node"]])),
        combo=combo,
        famiglia=famiglia_by_combo.get(combo),
        fx_kN=float(item[index["FX"]]) * force_factor,
        fy_kN=float(item[index["FY"]]) * force_factor,
        fz_kN=float(item[index["FZ"]]) * force_factor,
        mx_kNm=float(item[index["MX"]]) * moment_fac,
        my_kNm=float(item[index["MY"]]) * moment_fac,
        mz_kNm=float(item[index["MZ"]]) * moment_fac,
    )


def _strip_suffix(name: str) -> str:
    """`"SLU1(CB)"` -> `"SLU1"` (§1 "Load case names in tables carry the analysis suffix")."""
    return _SUFFIX_RE.sub("", name)


def _chunks(seq: tuple[str, ...], size: int) -> tuple[tuple[str, ...], ...]:
    return tuple(seq[i : i + size] for i in range(0, len(seq), size))


def _truncate(rows: tuple[ReactionRow, ...]) -> tuple[tuple[ReactionRow, ...], tuple[str, ...]]:
    if len(rows) <= MAX_REAZIONI_ROWS:
        return rows, ()
    warning = f"Troncato a {MAX_REAZIONI_ROWS} righe (ricevute {len(rows)})."
    return rows[:MAX_REAZIONI_ROWS], (warning,)

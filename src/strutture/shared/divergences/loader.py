"""Load and validate the register from the packaged JSON files."""
import functools
import json
from pathlib import Path

from .models import Divergence

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "divergences"


def parse_file(path: Path) -> tuple[Divergence, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError(f"{path.name}: expected a JSON list of divergences")
    items = tuple(Divergence.model_validate(entry) for entry in raw)
    wrong_unit = [d.id for d in items if d.id.split("/", 1)[0] != path.stem]
    if wrong_unit:
        raise ValueError(f"{path.name}: ids must start with '{path.stem}/': {wrong_unit}")
    return items


@functools.lru_cache(maxsize=1)
def load_register(data_dir: Path = DATA_DIR) -> tuple[Divergence, ...]:
    """Every divergence of every unit, sorted by id; duplicate ids are an error."""
    items = tuple(d for path in sorted(data_dir.glob("*.json")) for d in parse_file(path))
    seen: set[str] = set()
    duplicates = {d.id for d in items if d.id in seen or seen.add(d.id)}
    if duplicates:
        raise ValueError(f"duplicate divergence ids: {sorted(duplicates)}")
    return tuple(sorted(items, key=lambda d: d.id))


def register_by_id(data_dir: Path = DATA_DIR) -> dict[str, Divergence]:
    return {d.id: d for d in load_register(data_dir)}

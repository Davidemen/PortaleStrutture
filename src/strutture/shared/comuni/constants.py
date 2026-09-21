"""Domain constants for the merged Comuni database (architecture.md §3, conflict C3)."""
from pathlib import Path

CSV_FIELDNAMES: tuple[str, ...] = (
    "regione", "provincia", "istat", "comune", "zona_sismica", "zona_vento", "zona_neve",
)

VALID_ZONA_SISMICA: frozenset[str] = frozenset({"1", "2", "3", "4"})
VALID_ZONA_VENTO: frozenset[str] = frozenset({"1", "2", "3", "4", "5", "6", "7", "8", "9"})
VALID_ZONA_NEVE: frozenset[str] = frozenset({"I (alpina)", "I (mediterranea)", "II", "III"})

# src/strutture/shared/comuni/constants.py -> parent(comuni) -> parent(shared) -> parent(strutture) -> data/
DATA_CSV_PATH: Path = Path(__file__).resolve().parent.parent.parent / "data" / "comuni.csv"

DEFAULT_SEARCH_LIMIT: int = 10

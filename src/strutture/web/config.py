"""Runtime configuration for the web app, read from environment variables."""
import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_RATE_LIMIT_PER_MINUTE = 600  # live recalculation while typing: ~2 requests/s per engineer
_DEFAULT_MAX_BODY_BYTES = 8_000_000  # 8 MB: a 20 000-row reactions table is ~3 MB of JSON
DEFAULT_STATIC_DIR = Path(__file__).parent / "static"
# src/strutture/web/config.py -> parents[3] is the project root; never inside the package, never in git.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "var"


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot; build with `from_env()`."""

    rate_limit_per_minute: int
    max_body_bytes: int
    host: str
    port: int
    static_dir: Path = DEFAULT_STATIC_DIR
    data_dir: Path = DEFAULT_DATA_DIR


def from_env(env: dict[str, str] | None = None) -> Settings:
    """Build settings from environment variables, falling back to sane defaults."""
    source = env if env is not None else os.environ
    return Settings(
        rate_limit_per_minute=_positive_int(source.get("STRUTTURE_WEB_RATE_LIMIT"), _DEFAULT_RATE_LIMIT_PER_MINUTE),
        max_body_bytes=_positive_int(source.get("STRUTTURE_WEB_MAX_BODY_BYTES"), _DEFAULT_MAX_BODY_BYTES),
        host=source.get("STRUTTURE_WEB_HOST", "127.0.0.1"),
        port=_positive_int(source.get("STRUTTURE_WEB_PORT"), 8000),
        static_dir=_static_dir(source.get("STRUTTURE_WEB_STATIC_DIR")),
        data_dir=_data_dir(source.get("STRUTTURE_DATA_DIR")),
    )


def _static_dir(raw: str | None) -> Path:
    """Directory holding index.html; a staging copy can be served via STRUTTURE_WEB_STATIC_DIR."""
    if raw is None:
        return DEFAULT_STATIC_DIR
    path = Path(raw).expanduser().resolve()
    if not (path / "index.html").is_file():
        raise ValueError(f"STRUTTURE_WEB_STATIC_DIR={raw!r}: no index.html found in {path}")
    return path


def _data_dir(raw: str | None) -> Path:
    """Directory holding the SQLite database; created on first use by the repository, not here."""
    if raw is None:
        return DEFAULT_DATA_DIR
    return Path(raw).expanduser().resolve()


def _positive_int(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default

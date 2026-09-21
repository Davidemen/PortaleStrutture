"""Convert legacy .xls to .xlsx with headless LibreOffice (keeps formulas; xlrd cannot read them)."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import SOFFICE_CANDIDATES, XLSX_DIR

CONVERT_TIMEOUT_S = 300


def profile_argument(profile_dir: Path) -> str:
    """LibreOffice wants the private profile as a file URI (file:///C:/… on Windows), never a raw path."""
    return f"-env:UserInstallation={profile_dir.resolve().as_uri()}"


def find_soffice() -> str:
    for candidate in SOFFICE_CANDIDATES:
        resolved = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if resolved:
            return str(resolved)
    raise FileNotFoundError("LibreOffice not found; install with: brew install --cask libreoffice")


def to_xlsx(source: Path) -> Path:
    """Return an .xlsx path holding the workbook's formulas (the source itself if already xlsx)."""
    if source.suffix.lower() == ".xlsx":
        return source
    target = XLSX_DIR / f"{source.stem}.xlsx"
    if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
        return target
    XLSX_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:  # private profile: safe next to other soffice runs
        result = subprocess.run(
            [find_soffice(), "--headless", profile_argument(Path(profile)),
             "--convert-to", "xlsx", "--outdir", str(XLSX_DIR), str(source)],
            capture_output=True, text=True, timeout=CONVERT_TIMEOUT_S, check=False,
        )
    if result.returncode != 0 or not target.exists():
        raise RuntimeError(f"conversion failed for {source.name}: {result.stderr.strip() or result.stdout.strip()}")
    return target

"""Paths and tuning constants for the workbook extraction pipeline."""
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
XLSX_DIR = BUILD / "xlsx"
CELLMAP_DIR = BUILD / "cellmaps"
DATA_DIR = BUILD / "data"
MEDIA_DIR = BUILD / "media"
REPORT_PATH = BUILD / "report.md"
WORKBOOK_DIRS = (ROOT, ROOT / "workbooks")  # batch 1 lives in the root, later batches in workbooks/
WORKBOOK_SUFFIXES = (".xls", ".xlsx")

SOFFICE_CANDIDATES = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",          # macOS
    r"C:\Program Files\LibreOffice\program\soffice.exe",             # Windows
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "soffice",                                                        # anything on PATH (Linux, custom installs)
)

MAX_TEXT_LEN = 80
FORMULA_RUN_MIN = 6   # consecutive fill-down rows before compressing
CONST_RUN_MIN = 25    # consecutive constant-only table rows before compressing
RUN_HEAD_ROWS = 2
VALUE_REL_TOL = 1e-9

WORKBOOK_SLUGS = {
    "Azione sismica da NTC - DM2018": "sisma",
    "Carico neve da NTC - DM2018": "neve",
    "Carico vento da NTC - DM2018": "vento",
    "Coefficienti Cpe Vento - DM2018": "vento-cpe",
    "Calcolo travi in c.a. secondo NTC - DM2008": "ca-travi",
    "Calcolo pilastri in c.a. secondo NTC - DM2008": "ca-pilastri",
    "Calcolo mensole tozze in c.a. secondo NTC - DM2008": "ca-mensole",
    "Taglio non armato NTC2018": "ca-taglio-non-armato",
    "Verifica fessurazione - SLEF (X)": "ca-fessurazione",
    "Muro di sostegno DM2018": "muro-sostegno",
    "Resistenza acciaio con incendio": "acciaio-incendio",
    "Verifica instabilità e resistenza colonne ad H secondo EC3": "acciaio-colonne-ec3",
    # batch 2 (workbooks/)
    "2xxxx_Cedimenti fondazioni_elastico+edo": "geo-cedimenti",
    "2xxxx_Plinti isolati": "fond-plinti-isolati",
    "2xxxx_Plinti su pali_PL-FX_S&T Eurocode 2": "fond-plinti-pali",
    "2xxxx_Punzonamento - EC2 §6.4": "ca-punzonamento",
    "2xxxx_Taglio non armato NTC2018": "ca-taglio-non-armato-v2",
    "2xxxx_Verifiche al fuoco_proprietà materiali": "fuoco-materiali",
    "10x_Pavimento industriale CNR_DT211-2014": "pavimento-industriale",
    "30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019": "ca-pilastri-ntc2018",
    "31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005": "ca-pilastri-ec2",
    "50_Calcolo travi di collegamento NTC 2018": "fond-travi-collegamento",
    "2xxx_Sezione H rimpiattata": "acciaio-sezione-h-rimpiattata",
}


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def workbook_slug(path: Path) -> str:
    stem = unicodedata.normalize("NFC", path.stem)
    return WORKBOOK_SLUGS.get(stem, slugify(stem))


def workbook_sources() -> tuple[Path, ...]:
    """Every workbook of every batch, sorted by slug (Excel lock files '~$…' excluded)."""
    found = (
        p
        for directory in WORKBOOK_DIRS
        if directory.is_dir()
        for p in directory.iterdir()
        if p.suffix.lower() in WORKBOOK_SUFFIXES and not p.name.startswith("~")
    )
    return tuple(sorted(found, key=workbook_slug))

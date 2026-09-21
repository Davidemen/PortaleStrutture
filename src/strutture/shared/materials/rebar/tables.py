"""Union roster of rebar grades (merge C1, docs/architecture.md §3): ca-travi!Tabelle M45:P50 has
B450C/FeB22k/FeB32k/FeB38k/FeB44k/RB500W; ca-mensole!Tabelle M45:P47 swaps FeB22k for B500C;
ca-pilastri!Tabelle M45:P49 has B450C/FeB22k/FeB32k/FeB38k/FeB44k only. B450A: same sheets, rows
52-58 (no σamm in any sheet)."""
from .models import RebarGrade

# fyk, ftk, σamm (N/mm²) per grade — union of all three Tabelle sheets.
REBAR_TABLE_MPA: tuple[tuple[RebarGrade, tuple[float, float, float | None]], ...] = (
    ("B450C", (450.0, 540.0, 225.0)),
    ("B450A", (450.0, 540.0, None)),
    ("B500C", (500.0, 600.0, 400.0)),
    ("FeB22k", (215.0, 335.0, 115.0)),
    ("FeB32k", (315.0, 490.0, 155.0)),
    ("FeB38k", (375.0, 450.0, 215.0)),
    ("FeB44k", (430.0, 540.0, 255.0)),
    ("RB500W", (500.0, 650.0, 280.0)),
)

# NTC2018 §11.3.2 Tab. 11.3.Ia — unici gradi ammessi per armature ordinarie in opere nuove.
CURRENT_NTC_GRADES: frozenset[RebarGrade] = frozenset({"B450C", "B450A"})

ES_MPA = 210000.0  # NTC2018 §11.3.2.1 — modulo elastico dell'acciaio da cemento armato.
GAMMA_S = 1.15  # NTC2018 Tab. 4.1.II (ca-travi!Tabelle E4) — coefficiente di sicurezza dell'acciaio.

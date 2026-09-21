"""Lookup tables read from sheet `Tabelle` (NTC2018 §3.3): zona vento -> vb0/a0/ka/ks; categoria -> kr/z0/zmin."""
from strutture.shared.tables import exact_lookup

# Tabelle!A3:D11 (zona vento 1-9) -> (vb,0 [m/s], a0 [m], ka [1/s], ks [-]).
# ka: coefficiente della forma NTC2008 superata (Vento!H10), riprodotto solo in legacy_compat.
# ks: NTC2018 Tab. 3.3.I (§3.3.2), usato per ca in modalità standard (legacy_compat=False).
ZONA_TABLE: tuple[tuple[int, tuple[float, float, float, float]], ...] = (
    (1, (25.0, 1000.0, 0.01, 0.40)),
    (2, (25.0, 750.0, 0.015, 0.45)),
    (3, (27.0, 500.0, 0.02, 0.37)),
    (4, (28.0, 500.0, 0.02, 0.36)),
    (5, (28.0, 750.0, 0.015, 0.40)),
    (6, (28.0, 500.0, 0.02, 0.36)),
    (7, (28.0, 1000.0, 0.015, 0.54)),
    (8, (30.0, 1500.0, 0.01, 0.50)),
    (9, (31.0, 500.0, 0.02, 0.32)),
)

# Tabelle!A17:D21 (categoria di esposizione I-V) -> (kr [-], z0 [m], zmin [m])
CATEGORIA_TABLE: tuple[tuple[str, tuple[float, float, float]], ...] = (
    ("I", (0.17, 0.01, 2.0)),
    ("II", (0.19, 0.05, 4.0)),
    ("III", (0.20, 0.10, 5.0)),
    ("IV", (0.22, 0.30, 8.0)),
    ("V", (0.23, 0.70, 12.0)),
)


def zona_parametri(zona: int) -> tuple[float, float, float, float]:
    """vb0 [m/s], a0 [m], ka [1/s], ks [-] per la zona vento (Tabelle!A3:D11 + Tab. 3.3.I NTC2018)."""
    return exact_lookup(ZONA_TABLE, zona)


def categoria_parametri(categoria: str) -> tuple[float, float, float]:
    """kr [-], z0 [m], zmin [m] per la categoria di esposizione (Tabelle!A17:D21)."""
    return exact_lookup(CATEGORIA_TABLE, categoria)

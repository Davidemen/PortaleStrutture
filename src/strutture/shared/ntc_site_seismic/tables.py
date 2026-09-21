"""Lookup tables for the NTC 2018 site/seismic chain (Sisma!Tabelle; Tab. 2.4.II coefficiente
d'uso, Tab. 3.2.IV espressioni Ss/Cc, Tab. 3.2.V valori ST)."""
from .models import CategoriaTopografica, ClasseUso, StatoLimite

# Tabelle!C2:F3 (Tab. 2.4.II) — coefficiente d'uso Cu by classe d'uso.
COEFFICIENTE_USO: tuple[tuple[ClasseUso, float], ...] = (
    ("I", 0.7),
    ("II", 1.0),
    ("III", 1.5),
    ("IV", 2.0),
)

# Tabelle!A7:B10 (Tab. 3.2.V) — fattore di amplificazione topografica ST.
FATTORE_TOPOGRAFICO_ST: tuple[tuple[CategoriaTopografica, float], ...] = (
    ("T1", 1.0),
    ("T2", 1.2),
    ("T3", 1.2),
    ("T4", 1.4),
)

# NTC2018 §3.2.1 eq. 3.2.1 — probabilità di superamento PVR by stato limite.
PROBABILITA_SUPERAMENTO_PVR: tuple[tuple[StatoLimite, float], ...] = (
    ("SLO", 0.81),
    ("SLD", 0.63),
    ("SLV", 0.10),
    ("SLC", 0.05),
)

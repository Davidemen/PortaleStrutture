"""Drawing primitives for live element sketches (footing plan, wall section, bar layout, …).

A tool computes a `Sketch` from its inputs/results in pure Python (`<tool>/schizzo.py`) and returns it
in an output field `schizzo: Sketch | None` with the hint `widget: "sketch"`. The web UI has ONE
generic renderer that fits each view into its box and draws SVG — no per-tool UI code, and the same
data feeds the printed relazione.

Conventions: model coordinates in metres, x to the right, y UP (the renderer flips). Styles are
semantic (the UI owns colours and line weights).

COMPOSITION RULES (user feedback: sketches were "messy and cramped"; enforced by
`tests/shared/test_sketch_layout.py` — layout, readability and text-overlap lints over every tool):
1. A sketch is a SCHEMA, not a scale drawing. When true proportions are unreadable, draw schematically and
   say so in `Sketch.nota` ("Schema non in scala"). Keep each view between 1:3.5 and 3.5:1: crop a long
   element to ~1.4x the region of interest and end it with a short `fantasma` dashed continuation.
2. No slivers: a solid thinner than 2 % of the view's larger side gets a schematic minimum thickness (~3 %).
3. Offsets scale with the view: dimension `distanza` = 6-8 % of the view's larger side (never a fixed
   0.3 m); chained dimensions step outward by the same amount.
4. Labels: with `simbolo` set, `testo` is the VALUE ONLY ("6,16 kN/m²", never "q_s2 = 6,16 kN/m²").
   One label per fact, outside the solids, on the side with free space, anchored so the text grows away
   from the element. At most 8 text items per view: secondary values belong in the results, not here.
5. No two texts may overlap at the size the UI draws them (11.5 px in a ~340x220 px cell).
6. Loads and pressures as filled shapes (Diagramma / Poligono `pressione`) with the peak labelled AT the
   peak; zero ends stay unlabelled.

SIDE CONVENTION (easy to get backwards — `tests/shared/test_sketch_layout.py` checks every tool):
the "left" of a segment p1 -> p2 is its left-hand normal `normale_sinistra(p1, p2)` = (-dy, dx)/len.
- `Quota.distanza` > 0 puts the dimension line on the LEFT of p1 -> p2, < 0 on the right. Dimension
  the bottom edge of a footing from left to right ((0,0) -> (B,0)): left = up = INSIDE the footing,
  so use a NEGATIVE distanza to place the line below it. Dimension lines always go outside the element.
- `Diagramma` ordinates (positive `valori`) are drawn on the LEFT of base[0] -> base[1]. Soil pressure
  under a base must hang BELOW it: run the baseline from RIGHT to LEFT ((B,0) -> (0,0)). Texts are final Italian strings: use `etichetta_quota` (NOT named test*: pytest would collect it).
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Punto = tuple[float, float]
Stile = Literal[
    "calcestruzzo", "terreno", "acciaio", "armatura", "palo", "acqua",
    "carico", "reazione", "pressione", "puntone", "tirante",
    "quota", "asse", "evidenza", "fantasma",
]
Ancora = Literal["start", "middle", "end"]
MAX_SHAPES = 400
MAX_VIEWS = 4


class _Forma(BaseModel):
    model_config = ConfigDict(frozen=True)


class Rettangolo(_Forma):
    kind: Literal["rect"] = "rect"
    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)
    stile: Stile


class Poligono(_Forma):
    kind: Literal["polygon"] = "polygon"
    punti: tuple[Punto, ...] = Field(min_length=3)
    stile: Stile


class Cerchio(_Forma):
    kind: Literal["circle"] = "circle"
    centro: Punto
    r: float = Field(gt=0)
    stile: Stile
    tratteggio: bool = False  # dashed outline, no fill (e.g. radius of relative stiffness, control perimeters)


class Linea(_Forma):
    kind: Literal["line"] = "line"
    p1: Punto
    p2: Punto
    stile: Stile
    tratteggio: bool = False


class Freccia(_Forma):
    """A force/load vector from `coda` to `punta`; `testo` e.g. "N = 850 kN"."""

    kind: Literal["arrow"] = "arrow"
    coda: Punto
    punta: Punto
    stile: Stile = "carico"
    testo: str = ""
    campo: str | None = None  # input field this text stands for (see Quota.campo)


class Quota(_Forma):
    """Dimension line between p1 and p2, drawn `distanza` (metres, + = left of p1->p2) away from them."""

    kind: Literal["dimension"] = "dimension"
    p1: Punto
    p2: Punto
    distanza: float
    testo: str
    # Name of the INPUT field this dimension stands for, when the UI cannot infer it from the text
    # (js/schizzo-modifica.js matches "<symbol> = <value> <unit>" against the fields' symbol and
    # unit; set this where the sketch prints another symbol or unit than the field carries). The
    # UI then lets the user edit that field from the drawing.
    campo: str | None = None


class Etichetta(_Forma):
    kind: Literal["label"] = "label"
    punto: Punto
    testo: str = ""
    simbolo: str | None = None  # rendered with subscripts, e.g. "σ_max"
    ancora: Ancora = "start"
    stile: Stile = "asse"
    campo: str | None = None  # input field this label stands for (see Quota.campo)


class Barre(_Forma):
    """Reinforcing bars (or piles in plan) as filled circles of real diameter."""

    kind: Literal["bars"] = "bars"
    centri: tuple[Punto, ...] = Field(min_length=1)
    diametro: float = Field(gt=0)
    stile: Stile = "armatura"


class Diagramma(_Forma):
    """Ordinates plotted perpendicular to a baseline (soil pressure, moment, stress block).
    The renderer scales the largest |valore| to `altezza_relativa` of the view's smaller side."""

    kind: Literal["diagram"] = "diagram"
    base: tuple[Punto, Punto]
    valori: tuple[float, ...] = Field(min_length=2)
    etichette: tuple[str, ...] = ()
    stile: Stile = "pressione"
    altezza_relativa: float = Field(default=0.25, gt=0, le=0.6)


Forma = Annotated[
    Rettangolo | Poligono | Cerchio | Linea | Freccia | Quota | Etichetta | Barre | Diagramma,
    Field(discriminator="kind"),
]


class Vista(BaseModel):
    model_config = ConfigDict(frozen=True)

    titolo: str  # "Pianta", "Sezione A-A"
    forme: tuple[Forma, ...] = Field(min_length=1, max_length=MAX_SHAPES)


class Sketch(BaseModel):
    model_config = ConfigDict(frozen=True)

    viste: tuple[Vista, ...] = Field(min_length=1, max_length=MAX_VIEWS)
    nota: str = ""


def etichetta_quota(simbolo: str, valore: float, unita: str, decimali: int = 2) -> str:
    """'B = 2,40 m' — Italian decimal comma, fixed decimals."""
    numero = f"{valore:.{decimali}f}".replace(".", ",")
    return f"{simbolo} = {numero} {unita}".strip()


def campo_schizzo() -> object:
    """`Field(...)` for the output field: `schizzo: Sketch | None = campo_schizzo()`."""
    return Field(default=None, description="Schizzo dell'elemento", json_schema_extra={"widget": "sketch"})


def normale_sinistra(p1: Punto, p2: Punto) -> Punto:
    """Unit left-hand normal of the segment p1 -> p2 (y up): the side a positive offset goes to."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    lunghezza = (dx * dx + dy * dy) ** 0.5
    if lunghezza == 0:
        raise ValueError("segmento di lunghezza nulla")
    return (-dy / lunghezza, dx / lunghezza)


def linea_quota(quota: Quota) -> tuple[Punto, Punto]:
    """End points of the dimension LINE (the measured segment shifted by `distanza`)."""
    nx, ny = normale_sinistra(quota.p1, quota.p2)
    d = quota.distanza
    return ((quota.p1[0] + nx * d, quota.p1[1] + ny * d), (quota.p2[0] + nx * d, quota.p2[1] + ny * d))

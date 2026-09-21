"""Drawing primitives for live element sketches (footing plan, wall section, bar layout, …).

A tool computes a `Sketch` from its inputs/results in pure Python (`<tool>/schizzo.py`) and returns it
in an output field `schizzo: Sketch | None` with the hint `widget: "sketch"`. The web UI has ONE
generic renderer that fits each view into its box and draws SVG — no per-tool UI code, and the same
data feeds the printed relazione.

Conventions: model coordinates in metres, x to the right, y UP (the renderer flips). Styles are
semantic (the UI owns colours and line weights). Texts are final Italian strings: use `etichetta_quota` (NOT named test*: pytest would collect it).
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


class Quota(_Forma):
    """Dimension line between p1 and p2, drawn `distanza` (metres, + = left of p1->p2) away from them."""

    kind: Literal["dimension"] = "dimension"
    p1: Punto
    p2: Punto
    distanza: float
    testo: str


class Etichetta(_Forma):
    kind: Literal["label"] = "label"
    punto: Punto
    testo: str = ""
    simbolo: str | None = None  # rendered with subscripts, e.g. "σ_max"
    ancora: Ancora = "start"
    stile: Stile = "asse"


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

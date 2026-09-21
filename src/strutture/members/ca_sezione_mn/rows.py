"""Table row models for `ca-sezione-dominio-mn` (docs/architecture-phase4.md §B): reinforcement
bars, free-polygon outline vertices and N-M load combinations. Every row is frozen/flat/scalar per
`shared.tabular.RowModel` (docs/BUILD_CONTRACT.md "Batch 2").

Polo (origin): `sezione_builder.costruisci_sezione` ALWAYS recentres the section on the centroid of
the concrete outline before computing anything, regardless of `forma` — so `x_mm`/`y_mm` below can
be typed in ANY consistent frame (e.g. copied straight from a CAD drawing), and `AzioneRow.n_ed_kN`/
`m_ed_x_kNm`/`m_ed_y_kNm` must always be referred to the section's own centroid (never to the frame
the bars/vertices happen to be typed in).

Sign convention (`shared/sezione_ca/integrazione.py::risultante_sezione`, `Risultante`'s own
docstring for `N`/`M`, `M_Ed,y` derived here the same way): `N_Ed > 0` compression; `M_Ed,x > 0`
tends the fibre at minimum y (bottom); `M_Ed,y > 0` tends the fibre at maximum x — equivalently,
the pair `(M_Ed,x, M_Ed,y)` is the OPPOSITE of the right-handed bending-moment components about
(x, y)."""
from pydantic import ConfigDict, Field

from strutture.shared.tabular import RowModel

MAX_BARRE_ROWS = 200
MAX_VERTICI_ROWS = 50
MAX_AZIONI_ROWS = 500


class BarraRow(RowModel):
    """Una barra d'armatura in tabella: posizione nel piano della sezione e diametro."""

    model_config = ConfigDict(frozen=True)

    x_mm: float = Field(
        description="Ascissa del baricentro della barra, in un sistema di riferimento qualsiasi "
                    "coerente col contorno (la sezione viene ricentrata sul proprio baricentro "
                    "prima del calcolo: l'origine scelta qui non incide sul risultato)",
        json_schema_extra={"unit": "mm", "symbol": "x"},
    )
    y_mm: float = Field(
        description="Ordinata del baricentro della barra, nello stesso sistema di riferimento di x_mm",
        json_schema_extra={"unit": "mm", "symbol": "y"},
    )
    diametro_mm: float = Field(
        gt=0, le=60, description="Diametro della barra", json_schema_extra={"unit": "mm", "symbol": "φ"},
    )


class VerticeRow(RowModel):
    """Un vertice del contorno poligonale libero, in ordine (antiorario o orario: il verso viene
    normalizzato automaticamente in fase di calcolo)."""

    model_config = ConfigDict(frozen=True)

    x_mm: float = Field(
        description="Ascissa del vertice, in un sistema di riferimento qualsiasi (es. lo stesso del "
                    "disegno CAD): la sezione viene ricentrata sul proprio baricentro prima del calcolo",
        json_schema_extra={"unit": "mm", "symbol": "x"},
    )
    y_mm: float = Field(
        description="Ordinata del vertice, nello stesso sistema di riferimento di x_mm",
        json_schema_extra={"unit": "mm", "symbol": "y"},
    )


class AzioneRow(RowModel):
    """Una combinazione di carico da verificare a pressoflessione (N-Mx-My)."""

    model_config = ConfigDict(frozen=True)

    nome: str = Field(
        min_length=1, max_length=64, description="Nome della combinazione di carico",
        json_schema_extra={"unit": "-", "aliases": ["Nome", "Combo", "Combinazione"]},
    )
    n_ed_kN: float = Field(
        description="Sforzo normale di progetto (positivo se di compressione)",
        json_schema_extra={"unit": "kN", "symbol": "N_Ed", "aliases": ["N_Ed", "N", "Fz"]},
    )
    m_ed_x_kNm: float = Field(
        default=0.0,
        description="Momento flettente di progetto attorno all'asse x, riferito al baricentro della "
                    "sezione: positivo se tende la fibra di ordinata minima (lembo inferiore)",
        json_schema_extra={"unit": "kNm", "symbol": "M_Ed,x", "aliases": ["M_Ed,x", "Mx", "Mxx"]},
    )
    m_ed_y_kNm: float = Field(
        default=0.0,
        description="Momento flettente di progetto attorno all'asse y, riferito al baricentro della "
                    "sezione: positivo se tende la fibra di ascissa massima",
        json_schema_extra={"unit": "kNm", "symbol": "M_Ed,y", "aliases": ["M_Ed,y", "My", "Myy"]},
    )

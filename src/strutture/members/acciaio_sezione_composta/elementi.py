"""Build the list of rectangular elements (profile parts + reinforcing plates) as plain geometry.

Every element is a rectangle `b_mm` (horizontal extent) x `h_mm` (vertical extent) centred at
`(x_mm, y_mm)`. Downstream modules (baricentro, inerzia, plastico, moduli_elastici) only need this
flat geometric description — they never know whether an element is a flange, the web or a plate.
"""
from pydantic import BaseModel, ConfigDict, Field

from .models import PiattoRow


class Elemento(BaseModel):
    """One rectangular element of the composite section."""

    model_config = ConfigDict(frozen=True)

    nome: str = Field(description="Etichetta dell'elemento")
    b_mm: float = Field(description="Larghezza (estensione orizzontale); 0 = piatto disattivato", ge=0)
    h_mm: float = Field(description="Altezza (estensione verticale); 0 = piatto disattivato", ge=0)
    x_mm: float = Field(description="Ascissa del baricentro dell'elemento rispetto all'asse dell'anima")
    y_mm: float = Field(description="Ordinata del baricentro dell'elemento rispetto alla base del profilo")

    @property
    def area_mm2(self) -> float:
        return self.b_mm * self.h_mm


ALTEZZA_ANIMA_RIFERIMENTO_LEGACY_MM = 114.0  # sheet's C7 = "114-2*C6": hard-coded instead of B1


def elementi_profilo(h_profilo_mm: float, b_profilo_mm: float, tf_mm: float, tw_mm: float,
                      *, y_ala_inferiore_legacy: float | None = None,
                      altezza_riferimento_anima_mm: float | None = None) -> tuple[Elemento, ...]:
    """The three base elements of the H/I profile: top flange, web, bottom flange (A1/A2/A3).

    `y_ala_inferiore_legacy`, when given, reproduces the sheet's F8 fragility: the bottom flange
    centroid is `=+B9/2` — the first plate's own thickness used as a proxy for `tf/2` — instead of
    `tf_mm/2`. Harmless only while the first plate's thickness equals `tf_mm` (the sheet's
    default); a genuine sheet bug otherwise, see docs/divergences.

    `altezza_riferimento_anima_mm`, when given, reproduces the sheet's C7 fragility: the web clear
    height (hence the web's and top flange's vertical position) is computed from a hard-coded
    114 mm instead of the actual `h_profilo_mm` (B1) — see docs/divergences."""
    riferimento_anima = h_profilo_mm if altezza_riferimento_anima_mm is None else altezza_riferimento_anima_mm
    y_ala_inferiore = tf_mm / 2.0 if y_ala_inferiore_legacy is None else y_ala_inferiore_legacy
    h_anima = riferimento_anima - 2.0 * tf_mm
    # The web/top-flange placement assumes the bottom flange spans [0, tf_mm] (its true own
    # thickness, C8 in the sheet) regardless of `y_ala_inferiore_legacy`'s own bug.
    y_anima = h_anima / 2.0 + tf_mm
    y_ala_superiore = tf_mm / 2.0 + h_anima + tf_mm
    return (
        Elemento(nome="Ala superiore", b_mm=b_profilo_mm, h_mm=tf_mm, x_mm=0.0, y_mm=y_ala_superiore),
        Elemento(nome="Anima", b_mm=tw_mm, h_mm=h_anima, x_mm=0.0, y_mm=y_anima),
        Elemento(nome="Ala inferiore", b_mm=b_profilo_mm, h_mm=tf_mm, x_mm=0.0, y_mm=y_ala_inferiore),
    )


def _piatti_attivi(piatti: tuple[PiattoRow, ...]) -> tuple[PiattoRow, ...]:
    return tuple(p for p in piatti if p.b_mm > 0.0 and p.h_mm > 0.0)


def elementi_piatti_generale(piatti: tuple[PiattoRow, ...], h_profilo_mm: float,
                              b_profilo_mm: float) -> tuple[Elemento, ...]:
    """Plates welded to the flange tips, alternating sides and stacking outward on the same side.

    Row 0 goes on the +x side flush against the flange tip, row 1 on the -x side, row 2 stacks
    outward on the +x side beyond row 0, and so on. This is the natural generalisation of the
    sheet's A4 (+x)/A5 (-x, mirrored) pair when there are more than two plates."""
    attivi = _piatti_attivi(piatti)
    y_mm = h_profilo_mm / 2.0
    accumulo_lato: dict[int, float] = {1: b_profilo_mm / 2.0, -1: b_profilo_mm / 2.0}
    elementi: tuple[Elemento, ...] = ()
    for indice, piatto in enumerate(attivi):
        lato = 1 if indice % 2 == 0 else -1
        x_mm = lato * (accumulo_lato[lato] + piatto.b_mm / 2.0)
        accumulo_lato[lato] += piatto.b_mm
        elementi = (*elementi, Elemento(nome=f"Piatto {indice + 1}", b_mm=piatto.b_mm, h_mm=piatto.h_mm,
                                         x_mm=x_mm, y_mm=y_mm))
    return elementi


_PIATTO_ASSENTE = PiattoRow(b_mm=0.0, h_mm=0.0)


def elementi_piatti_legacy(piatti: tuple[PiattoRow, ...], h_profilo_mm: float,
                            b_profilo_mm: float) -> tuple[Elemento, ...]:
    """Reproduces the sheet's exact A4/A5 formulas: the A5 x offset mirrors A4's literally
    (`E10=-E9`), regardless of A5's own width — a latent sheet fragility, harmless while the two
    plates share the same width (the sheet's default). Both physical slots are always returned,
    even when disabled (`b_mm=0`, area 0): the sheet's baricentro formula always references row 10
    by fixed cell address (H6 bug, see baricentro.py), so slot A5 must keep its fixed position in
    the element list regardless of whether it is active."""
    y_mm = h_profilo_mm / 2.0
    piatto_a4 = piatti[0] if len(piatti) > 0 else _PIATTO_ASSENTE
    piatto_a5 = piatti[1] if len(piatti) > 1 else _PIATTO_ASSENTE
    offset_a4 = b_profilo_mm / 2.0 + piatto_a4.b_mm / 2.0
    return (
        Elemento(nome="Piatto 1", b_mm=piatto_a4.b_mm, h_mm=piatto_a4.h_mm, x_mm=offset_a4, y_mm=y_mm),
        Elemento(nome="Piatto 2", b_mm=piatto_a5.b_mm, h_mm=piatto_a5.h_mm, x_mm=-offset_a4, y_mm=y_mm),
    )


def costruisci_elementi(h_profilo_mm: float, b_profilo_mm: float, tf_mm: float, tw_mm: float,
                         piatti: tuple[PiattoRow, ...], *, legacy_compat: bool) -> tuple[Elemento, ...]:
    """All elements of the composite section, profile first then plates, in sheet order."""
    if legacy_compat:
        piatto_a4 = piatti[0] if piatti else _PIATTO_ASSENTE
        profilo = elementi_profilo(h_profilo_mm, b_profilo_mm, tf_mm, tw_mm,
                                    y_ala_inferiore_legacy=piatto_a4.b_mm / 2.0,
                                    altezza_riferimento_anima_mm=ALTEZZA_ANIMA_RIFERIMENTO_LEGACY_MM)
        return profilo + elementi_piatti_legacy(piatti, h_profilo_mm, b_profilo_mm)
    profilo = elementi_profilo(h_profilo_mm, b_profilo_mm, tf_mm, tw_mm)
    return profilo + elementi_piatti_generale(piatti, h_profilo_mm, b_profilo_mm)

"""Step: resolve the flat `SezioneMnInput` fields into the engine's `Sezione` (contour + bars +
materials), reusing `shared.sezione_ca.forme` presets — never re-deriving geometry the engine
already offers (docs/architecture-phase4.md §A/§B). Geometric error messages (degenerate/self-
intersecting outline, bar outside the outline) are the engine's own Italian text, only wrapped into
a `CalcError` for the tool contract.

`costruisci_sezione` ALWAYS recentres contour + bars on the raw contour's own centroid before
building the `Sezione` (finding CRITICO: `forme.sezione_a_t`/`sezione_a_l` do not put the origin at
the centroid — y=0 is the web's bottom fibre for the T, the outer corner for the L — and a free
polygon can be typed in any frame the engineer used on their drawing; the engine reduces N_Ed/M_Ed
about coordinate (0, 0), so an off-centroid origin silently shifts every M_Rd by N_Ed times the
polo's offset). After this step the origin is ALWAYS the centroid, for every `forma`: `N_Ed`,
`M_Ed,x` and `M_Ed,y` in `AzioneRow` must be referred to that same centroid (see its description)."""
from pydantic import ValidationError

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.report import CalcError
from strutture.shared.sezione_ca import forme
from strutture.shared.sezione_ca.geometria import Poligono, centroide, trasla
from strutture.shared.sezione_ca.modelli import Barra, MaterialiSezione, Sezione

from .models_input import SezioneMnInput

_LAYOUT_RETTANGOLARI = ("fila_superiore", "fila_inferiore", "perimetrale")


def costruisci_contorno(inputs: SezioneMnInput) -> Poligono:
    """Il contorno in cls per `inputs.forma`: i preset `shared.sezione_ca.forme` per le forme
    parametriche, i vertici in tabella per il poligono libero."""
    if inputs.forma == "rettangolare":
        return forme.rettangolo(inputs.b_mm, inputs.h_mm)  # type: ignore[arg-type]
    if inputs.forma == "circolare":
        return forme.cerchio(inputs.diametro_mm)  # type: ignore[arg-type]
    if inputs.forma == "a_t":
        return forme.sezione_a_t(inputs.bf_mm, inputs.hf_mm, inputs.bw_mm, inputs.h_mm)  # type: ignore[arg-type]
    if inputs.forma == "a_l":
        return forme.sezione_a_l(inputs.bf_mm, inputs.hf_mm, inputs.bw_mm, inputs.h_mm)  # type: ignore[arg-type]
    if inputs.forma == "parete":
        return forme.parete_con_elementi_estremita(inputs.lw_mm, inputs.tw_mm, inputs.le_mm, inputs.te_mm)  # type: ignore[arg-type]
    return tuple((v.x_mm, v.y_mm) for v in inputs.vertici)


def costruisci_barre(inputs: SezioneMnInput) -> tuple[Barra, ...]:
    """Le barre da tabella oppure dal layout parametrico scelto (già validati da
    `SezioneMnInput._valida_armatura`: nessun campo del layout richiesto è `None` qui)."""
    if inputs.armatura_modo == "tabella":
        return tuple(Barra(x_mm=r.x_mm, y_mm=r.y_mm, diametro_mm=r.diametro_mm) for r in inputs.barre)
    if inputs.layout_tipo in _LAYOUT_RETTANGOLARI and inputs.forma != "rettangolare":
        raise CalcError(f"il layout '{inputs.layout_tipo}' richiede una sezione rettangolare")
    if inputs.layout_tipo == "circolare" and inputs.forma != "circolare":
        raise CalcError("il layout 'circolare' richiede una sezione circolare")
    return _barre_layout(inputs)


def _barre_layout(inputs: SezioneMnInput) -> tuple[Barra, ...]:
    copriferro, diametro = inputs.layout_copriferro_mm, inputs.layout_diametro_mm
    if inputs.layout_tipo == "fila_superiore":
        return forme.fila_superiore(inputs.b_mm, inputs.h_mm, copriferro, inputs.layout_n_barre, diametro)  # type: ignore[arg-type]
    if inputs.layout_tipo == "fila_inferiore":
        return forme.fila_inferiore(inputs.b_mm, inputs.h_mm, copriferro, inputs.layout_n_barre, diametro)  # type: ignore[arg-type]
    if inputs.layout_tipo == "perimetrale":
        return forme.perimetrale(inputs.b_mm, inputs.h_mm, copriferro, inputs.layout_n_per_lato, diametro)  # type: ignore[arg-type]
    return forme.circolare(inputs.diametro_mm, copriferro, inputs.layout_n_barre, diametro)  # type: ignore[arg-type]


def costruisci_materiali(inputs: SezioneMnInput) -> MaterialiSezione:
    return MaterialiSezione(
        calcestruzzo=concrete_properties(inputs.classe_calcestruzzo),
        acciaio=rebar_properties(inputs.grado_acciaio),
        legge_calcestruzzo=inputs.legge_calcestruzzo,
        legge_acciaio=inputs.legge_acciaio,
    )


def _ricentra_sul_baricentro(contorno: Poligono, barre: tuple[Barra, ...]) -> tuple[Poligono, tuple[Barra, ...]]:
    cx, cy = centroide(contorno)
    contorno_centrato = trasla(contorno, -cx, -cy)
    barre_centrate = tuple(Barra(x_mm=b.x_mm - cx, y_mm=b.y_mm - cy, diametro_mm=b.diametro_mm) for b in barre)
    return contorno_centrato, barre_centrate


def costruisci_sezione(inputs: SezioneMnInput) -> Sezione:
    """La `Sezione` completa, pronta per il motore `shared.sezione_ca`: contorno e barre sono
    ricentrati sul baricentro del contorno grezzo (vedi il docstring del modulo) prima della
    costruzione."""
    contorno, barre = _ricentra_sul_baricentro(costruisci_contorno(inputs), costruisci_barre(inputs))
    try:
        return Sezione(contorno=contorno, barre=barre, materiali=costruisci_materiali(inputs))
    except ValidationError as error:
        messaggio = "; ".join(e["msg"].removeprefix("Value error, ") for e in error.errors())
        raise CalcError(messaggio) from error

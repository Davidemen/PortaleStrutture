"""Live sketch for `ca-punzonamento`: "Pianta" (loaded area/column, slab edge for bordo/angolo,
perimeters u0, the governing control perimeter and u0,out, distances a and 2d) —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + computed results; a failure
here must never fail the calculation (guarded in `compose.run`).

Rectangular control perimeters at distance `r_mm` from the column face are rounded rectangles
(EC2§6.4.2, `shared.ec2_shear.control_perimeter`): straight segments parallel to the column sides
plus a quarter-circle of radius `r_mm` at each corner, approximated here by a `Poligono` polyline.
Circular columns get an exact `Cerchio` instead.
"""
import math

from strutture.shared.sketch import Cerchio, Forma, Linea, Poligono, Quota, Rettangolo, Sketch, Vista, etichetta_quota
from strutture.shared.units import mm_to_m

from .effective_depth import column_shape
from .models import ArmaturaOutput, GeometriaOutput, PerimetroCriticoOutput, PunzonamentoInput

_N_PER_CORNER = 4  # punti per arco di raccordo d'angolo (rettangolo con smusso arrotondato)
_PASSO_QUOTE_FATTORE = 0.22  # passo tra le linee di quota impilate sotto la pianta, frazione della semilarghezza disegnata
_MARGINE_BORDO_FATTORE = 1.3  # il bordo di solaio va disegnato oltre il perimetro più esterno


def disegna(
    inputs: PunzonamentoInput, geometria: GeometriaOutput, perimetro_critico: PerimetroCriticoOutput,
    armatura: ArmaturaOutput | None,
) -> Sketch:
    """Pianta del pilastro/palo con i perimetri di verifica a punzonamento."""
    return Sketch(viste=(_pianta(inputs, geometria, perimetro_critico, armatura),))


def _raggio_colonna_x_mm(inputs: PunzonamentoInput) -> float:
    """Semiestensione della colonna in direzione x (raggio per il cerchio, lato_a/2 per il rettangolo)."""
    return inputs.diametro_mm / 2.0 if column_shape(inputs.lato_a_mm) == "circ" else inputs.lato_a_mm / 2.0


def _rounded_rect_points_mm(a_mm: float, b_mm: float, r_mm: float) -> tuple[tuple[float, float], ...]:
    """Rettangolo a spigoli arrotondati (raggio `r_mm`), centrato sull'origine."""
    ha, hb = a_mm / 2.0, b_mm / 2.0
    if r_mm <= 0.0:
        return ((ha, hb), (-ha, hb), (-ha, -hb), (ha, -hb))
    angoli = ((ha, hb, 0.0), (-ha, hb, 90.0), (-ha, -hb, 180.0), (ha, -hb, 270.0))
    punti: list[tuple[float, float]] = []
    for cx, cy, inizio_deg in angoli:
        for i in range(_N_PER_CORNER + 1):
            theta = math.radians(inizio_deg + 90.0 * i / _N_PER_CORNER)
            punti.append((cx + r_mm * math.cos(theta), cy + r_mm * math.sin(theta)))
    return tuple(punti)


def _perimetro(inputs: PunzonamentoInput, r_mm: float, stile: str, *, tratteggio: bool = False) -> Forma:
    """Un perimetro di verifica (u0, governante o u0,out) a distanza `r_mm` dal filo colonna.
    Per la colonna circolare i perimetri di sola verifica (u0, u0,out) sono tratteggiati per
    distinguerli dal contorno pieno della colonna e dal perimetro governante in evidenza."""
    if column_shape(inputs.lato_a_mm) == "circ":
        raggio_m = mm_to_m(inputs.diametro_mm / 2.0 + r_mm)
        return Cerchio(centro=(0.0, 0.0), r=raggio_m, stile=stile, tratteggio=tratteggio)
    punti_mm = _rounded_rect_points_mm(inputs.lato_a_mm, inputs.lato_b_mm, r_mm)
    return Poligono(punti=tuple((mm_to_m(x), mm_to_m(y)) for x, y in punti_mm), stile=stile)


def _colonna(inputs: PunzonamentoInput) -> Forma:
    if column_shape(inputs.lato_a_mm) == "circ":
        return Cerchio(centro=(0.0, 0.0), r=mm_to_m(inputs.diametro_mm / 2.0), stile="calcestruzzo")
    return Rettangolo(
        x=mm_to_m(-inputs.lato_a_mm / 2.0), y=mm_to_m(-inputs.lato_b_mm / 2.0),
        w=mm_to_m(inputs.lato_a_mm), h=mm_to_m(inputs.lato_b_mm), stile="calcestruzzo",
    )


def _bordo_solaio(inputs: PunzonamentoInput, margine_mm: float) -> tuple[Forma, ...]:
    """Bordo del solaio, schematico: un lato per `bordo`, due lati ortogonali per `angolo`. La
    lunghezza è proporzionata al disegno (non troppo oltre `margine_mm`): un tratto molto più
    lungo dilaterebbe l'estensione della vista percepita dal lint di leggibilità."""
    if inputs.posizione not in ("bordo", "angolo"):
        return ()
    span_m = mm_to_m(1.2 * margine_mm)
    x_bordo_m = mm_to_m(-margine_mm)
    verticale = Linea(p1=(x_bordo_m, -span_m / 2.0), p2=(x_bordo_m, span_m / 2.0), stile="quota")
    if inputs.posizione == "bordo":
        return (verticale,)
    y_bordo_m = mm_to_m(-margine_mm)
    orizzontale = Linea(p1=(-span_m / 2.0, y_bordo_m), p2=(span_m / 2.0, y_bordo_m), stile="quota")
    return (verticale, orizzontale)


def _raggio_colonna_y_mm(inputs: PunzonamentoInput) -> float:
    """Semiestensione della colonna in direzione y (raggio per il cerchio, lato_b/2 per il rettangolo)."""
    return inputs.diametro_mm / 2.0 if column_shape(inputs.lato_a_mm) == "circ" else inputs.lato_b_mm / 2.0


def _quote_a_2d(inputs: PunzonamentoInput, geometria: GeometriaOutput, a_governante_mm: float, estensione_mm: float) -> tuple[Quota, Quota]:
    """`a` e `2d` sono misurate dove stanno: dal filo della colonna lungo l'asse x fino alla
    distanza quotata. Le linee di quota sono portate SOTTO il perimetro più esterno (le linee di
    riferimento attraversano i perimetri, com'è normale in un disegno quotato; la linea di quota e
    il suo testo no) e impilate: `a` più vicina alla pianta, `2d` un passo più in basso."""
    filo_x_mm = _raggio_colonna_x_mm(inputs)
    fuori_y_mm = _raggio_colonna_y_mm(inputs) + estensione_mm  # semialtezza del perimetro più esterno
    passo_mm = _PASSO_QUOTE_FATTORE * (filo_x_mm + estensione_mm)
    due_d_mm = 2.0 * geometria.d_mm
    # verso +x la sinistra di p1->p2 è +y: distanza negativa = sotto la pianta (regola dei lati)
    quota_a = Quota(
        p1=(mm_to_m(filo_x_mm), 0.0), p2=(mm_to_m(filo_x_mm + a_governante_mm), 0.0),
        distanza=-mm_to_m(fuori_y_mm + passo_mm), testo=etichetta_quota("a_gov", a_governante_mm, "mm", 0),  # non "a": è il lato del pilastro (dato)
    )
    quota_2d = Quota(
        p1=(mm_to_m(filo_x_mm), 0.0), p2=(mm_to_m(filo_x_mm + due_d_mm), 0.0),
        distanza=-mm_to_m(fuori_y_mm + 2.0 * passo_mm), testo=etichetta_quota("2d", due_d_mm, "mm", 0),
    )
    return quota_a, quota_2d


def _pianta(
    inputs: PunzonamentoInput, geometria: GeometriaOutput, perimetro_critico: PerimetroCriticoOutput,
    armatura: ArmaturaOutput | None,
) -> Vista:
    """Ordine di disegno = ordine di stampa (paint order): il bordo di solaio e i perimetri di
    verifica (compreso quello governante, in evidenza) vanno disegnati PRIMA, la colonna/area
    caricata per ULTIMA, sopra di essi — altrimenti il riempimento del perimetro governante,
    più esteso, coprirebbe colonna e quote. Il renderer rende traslucidi i poligoni chiusi in
    stile "evidenza", quindi il perimetro governante resta leggibile come contorno anche se
    disegnato per primo fra i perimetri."""
    estensione_mm = max(perimetro_critico.a_governante_mm, armatura.k_d_primo_mm if armatura is not None else 0.0)
    margine_mm = _MARGINE_BORDO_FATTORE * (_raggio_colonna_x_mm(inputs) + estensione_mm)

    forme: list[Forma] = [
        *_bordo_solaio(inputs, margine_mm),
        _perimetro(inputs, 0.0, "quota", tratteggio=True),
        _perimetro(inputs, perimetro_critico.a_governante_mm, "evidenza"),
    ]
    if armatura is not None:
        forme.append(_perimetro(inputs, armatura.k_d_primo_mm, "quota", tratteggio=True))
    forme.append(_colonna(inputs))
    forme.extend(_quote_a_2d(inputs, geometria, perimetro_critico.a_governante_mm, estensione_mm))
    return Vista(titolo="Pianta", forme=tuple(forme))

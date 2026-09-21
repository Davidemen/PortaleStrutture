"""Live sketch for `fond-pavimento-industriale`: "Pianta" -- a slab panel sized by the
contraction-joint dimensions (`a_contrazione_m` x `b_contrazione_m`, the only slab-outline input
available), each `carichi` row's footprint (at a legible minimum schematic size) positioned per
`posizione`, one label per load listed OUTSIDE the panel (never on the outline), and the
Westergaard radius of relative stiffness `sott.l_mm` as a reference circle --
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + the subgrade radius already
computed in `tool.run`; a failure here must never fail the calculation (guarded in `tool.run`).

The reference radius -- not a real element -- is drawn as a dashed `Cerchio` (`tratteggio=True`,
no fill) via `stile="quota"`."""
from strutture.shared.sketch import Cerchio, Etichetta, Forma, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .carico_row import CaricoRow
from .models import PavimentoIndustrialeInput

_MARGINE_QUOTA = 0.07  # frazione del lato maggiore, per lo scostamento delle linee di quota (6-8 %)
_FRAZIONE_IMPRONTA_MINIMA = 0.03  # dimensione minima schematica di un'impronta, come frazione del pannello
_MARGINE_ETICHETTE_M = 0.5  # distanza dell'elenco etichette dal bordo destro del pannello
_PASSO_ETICHETTA_FRAZIONE = 0.1  # passo verticale fra etichette in elenco, come frazione del pannello
_MAX_ETICHETTE_CARICHI = 5  # etichette "caso" al massimo, indipendentemente dal numero di righe in tabella


def disegna(inputs: PavimentoIndustrialeInput, l_mm: float) -> Sketch:
    """Pianta della piastra (pannello di contrazione) con impronte di carico e raggio di Westergaard."""
    return Sketch(viste=(_pianta(inputs, l_mm),), nota="Schema non in scala")


def _pianta(inputs: PavimentoIndustrialeInput, l_mm: float) -> Vista:
    a, b = inputs.a_contrazione_m, inputs.b_contrazione_m
    scostamento = _MARGINE_QUOTA * max(a, b)
    forme: list[Forma] = [
        Rettangolo(x=-a / 2, y=-b / 2, w=a, h=b, stile="calcestruzzo"),
        Quota(p1=(-a / 2, b / 2), p2=(a / 2, b / 2), distanza=scostamento, testo=etichetta_quota("a'", a, "m")),
        Quota(p1=(a / 2, -b / 2), p2=(a / 2, b / 2), distanza=-scostamento, testo=etichetta_quota("b'", b, "m")),
        Cerchio(centro=(0.0, 0.0), r=l_mm / 1000.0, stile="quota", tratteggio=True),
    ]
    forme.extend(_impronte(inputs.carichi, a, b))
    forme.extend(_etichette_esterne(inputs.carichi, a, b))
    return Vista(titolo="Pianta", forme=tuple(forme))


def _basi_posizione(a: float, b: float) -> dict[str, tuple[float, float]]:
    """Punto di riferimento di ogni `posizione`: centro piastra, mezzeria del lato inferiore
    (l'impronta a cavallo del bordo) e spigolo inferiore sinistro (l'impronta a cavallo dello
    spigolo) -- la scelta del lato/spigolo e' arbitraria, equivalente per simmetria agli altri tre."""
    return {"centro": (0.0, 0.0), "bordo": (0.0, -b / 2), "spigolo": (-a / 2, -b / 2)}


def _impronte(carichi: tuple[CaricoRow, ...], a: float, b: float) -> tuple[Rettangolo, ...]:
    """Impronta per ogni riga, centrata sul punto della sua `posizione` (carichi realmente
    coincidenti, es. ruote di uno stesso mezzo, restano un'approssimazione accettabile ai fini del
    disegno). Disegnata a dimensione minima schematica: l'impronta reale (in mm) è spesso troppo
    piccola per essere visibile su un pannello di alcuni metri, altrimenti (nessun `stile` di
    sliver-check per "carico": la regola generale sulle sliver copre solo i solidi strutturali)."""
    basi = _basi_posizione(a, b)
    minimo = _FRAZIONE_IMPRONTA_MINIMA * max(a, b)
    forme: list[Rettangolo] = []
    for riga in carichi:
        w = max(riga.impronta_a_mm / 1000.0, minimo)
        h = max(riga.impronta_b_mm / 1000.0, minimo)
        base_x, base_y = basi[riga.posizione]
        forme.append(Rettangolo(x=base_x - w / 2, y=base_y - h / 2, w=w, h=h, stile="carico"))
    return tuple(forme)


def _etichette_esterne(carichi: tuple[CaricoRow, ...], a: float, b: float) -> tuple[Etichetta, ...]:
    """Un'etichetta per carico (al massimo `_MAX_ETICHETTE_CARICHI`), elencate fuori dal pannello
    (mai sul contorno) sul lato SINISTRO (le quote a'/b' occupano già il lato alto e destro), con
    il proprio valore P: uno scostamento fisso vicino all'impronta non basterebbe per
    "centro"/"bordo" (dentro o a cavallo del pannello)."""
    x = -(a / 2 + _MARGINE_ETICHETTE_M)
    passo = _PASSO_ETICHETTA_FRAZIONE * max(a, b)
    y_iniziale = (b / 2) - passo / 2
    forme: list[Etichetta] = []
    for indice, riga in enumerate(carichi[:_MAX_ETICHETTE_CARICHI]):
        testo = f"{riga.caso}, P {riga.p_kN:.0f} kN"
        forme.append(Etichetta(punto=(x, y_iniziale - indice * passo), testo=testo, ancora="end", stile="carico"))
    return tuple(forme)

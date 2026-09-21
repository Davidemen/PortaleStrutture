"""Live sketch for `fond-pavimento-industriale`: "Pianta" -- a slab panel sized by the
contraction-joint dimensions (`a_contrazione_m` x `b_contrazione_m`, the only slab-outline input
available), each `carichi` row's footprint positioned per `posizione`, and the Westergaard radius of
relative stiffness `sott.l_mm` as a reference circle -- docs/ui/WORKBENCH_SPEC.md §7. Pure function
of the validated inputs + the subgrade radius already computed in `tool.run`; a failure here must
never fail the calculation (guarded in `tool.run`).

The reference radius -- not a real element -- is drawn as a dashed `Cerchio` (`tratteggio=True`,
no fill) via `stile="quota"`."""
from strutture.shared.sketch import Cerchio, Etichetta, Forma, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .carico_row import CaricoRow
from .models import PavimentoIndustrialeInput

_MARGINE_QUOTA = 0.15  # frazione del lato maggiore, per lo scostamento delle linee di quota
_GAP_ETICHETTA_M = 0.05  # distanza verticale tra l'impronta e la sua etichetta
_GAP_SOVRAPPOSIZIONE_M = 0.05  # scostamento laterale tra impronte con la stessa posizione (affiancate)


def disegna(inputs: PavimentoIndustrialeInput, l_mm: float) -> Sketch:
    """Pianta della piastra (pannello di contrazione) con impronte di carico e raggio di Westergaard."""
    return Sketch(viste=(_pianta(inputs, l_mm),))


def _pianta(inputs: PavimentoIndustrialeInput, l_mm: float) -> Vista:
    a, b = inputs.a_contrazione_m, inputs.b_contrazione_m
    scostamento = _MARGINE_QUOTA * max(a, b)
    forme: list[Forma] = [
        Rettangolo(x=-a / 2, y=-b / 2, w=a, h=b, stile="calcestruzzo"),
        Quota(p1=(-a / 2, b / 2), p2=(a / 2, b / 2), distanza=scostamento, testo=etichetta_quota("a'", a, "m")),
        Quota(p1=(a / 2, -b / 2), p2=(a / 2, b / 2), distanza=-scostamento, testo=etichetta_quota("b'", b, "m")),
        Cerchio(centro=(0.0, 0.0), r=l_mm / 1000.0, stile="quota", tratteggio=True),
    ]
    forme.extend(_forme_carichi(inputs.carichi, a, b))
    return Vista(titolo="Pianta", forme=tuple(forme))


def _basi_posizione(a: float, b: float) -> dict[str, tuple[float, float]]:
    """Punto di riferimento di ogni `posizione`: centro piastra, mezzeria del lato inferiore
    (l'impronta a cavallo del bordo) e spigolo inferiore sinistro (l'impronta a cavallo dello
    spigolo) -- la scelta del lato/spigolo e' arbitraria, equivalente per simmetria agli altri tre."""
    return {"centro": (0.0, 0.0), "bordo": (0.0, -b / 2), "spigolo": (-a / 2, -b / 2)}


def _forme_carichi(carichi: tuple[CaricoRow, ...], a: float, b: float) -> tuple[Forma, ...]:
    """Impronta + etichetta per ogni riga della tabella. Righe con la stessa `posizione` (nell'esempio
    due carichi 'centro': ruota motrice e ruote anteriori) sono affiancate lungo x invece che
    sovrapposte, cosi' le etichette non si accavallano; carichi realmente coincidenti nella realta'
    (es. ruote di uno stesso mezzo) restano un'approssimazione accettabile ai fini del disegno."""
    basi = _basi_posizione(a, b)
    scostamenti = dict.fromkeys(basi, 0.0)
    forme: list[Forma] = []
    for riga in carichi:
        w, h = riga.impronta_a_mm / 1000.0, riga.impronta_b_mm / 1000.0
        base_x, base_y = basi[riga.posizione]
        cx = base_x + scostamenti[riga.posizione]
        forme.append(Rettangolo(x=cx - w / 2, y=base_y - h / 2, w=w, h=h, stile="carico"))
        forme.append(Etichetta(punto=(cx, base_y + h / 2 + _GAP_ETICHETTA_M), testo=riga.caso,
                                ancora="middle", stile="carico"))
        scostamenti[riga.posizione] += w + _GAP_SOVRAPPOSIZIONE_M
    return tuple(forme)

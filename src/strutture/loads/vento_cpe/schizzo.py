"""Live sketch for `vento-cpe-rettangolare`: two Vista, one per wind direction ("Pianta — direzione
1/2"), each the b×d plan rectangle with the windward/side/leeward face labels and dimensions —
docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in shared/sketch.py. Pure function of the validated
inputs + the computed cpe results; a failure here must never fail the calculation (guarded in
`tool.run`)."""
from strutture.shared.sketch import Etichetta, Freccia, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .models import DirectionResult, VentoCpeInput

_FRAZIONE_ETICHETTA = 0.22  # posizione dell'etichetta lungo il lato (non al centro: libera il centro
# per la freccia del vento e per il testo, centrato, della quota sullo stesso lato — regola 5)
_SCOSTAMENTO_ETICHETTA = 0.09  # frazione di max(b,d): distanza delle etichette c_pe fuori dal rettangolo
_MARGINE_QUOTA = 0.22  # frazione di max(b,d): distanza delle linee di quota dal rettangolo
_FRAZIONE_FRECCIA = 0.4  # frazione della dimensione lungo cui soffia il vento: coda della freccia fuori dal rettangolo

_Bordo = tuple[Punto, Punto]  # (punto di ancoraggio dell'etichetta sul lato, normale uscente unitaria)
_Bordi = tuple[_Bordo, _Bordo, _Bordo, _Bordo]  # (sopravento, laterale, laterale, sottovento)

_ASPETTO_MAX_DISEGNO = 3.0  # margine sotto il limite 3.5:1 del lint di leggibilità (regola 1)
NOTA_SCHEMA = "Schema non in scala: pianta compressa sul lato maggiore per restare leggibile."


def _dimensioni_disegnate(b: float, d: float) -> tuple[float, float, bool]:
    """(b_disegnato, d_disegnato, compresso): il lato maggiore è compresso quando il rapporto in
    pianta supera l'aspetto massimo leggibile; le quote riportano comunque i valori veri di b/d."""
    maggiore, minore = max(b, d), min(b, d)
    if minore <= 0 or maggiore / minore <= _ASPETTO_MAX_DISEGNO:
        return b, d, False
    lato_compresso = _ASPETTO_MAX_DISEGNO * minore
    return (lato_compresso, d, True) if b >= d else (b, lato_compresso, True)


def disegna(inputs: VentoCpeInput, dir1: DirectionResult, dir2: DirectionResult) -> Sketch:
    """Due piante b×d, una per direzione del vento, con le facce sopravento/laterali/sottovento.
    La geometria usa le dimensioni (eventualmente compresse) di `_dimensioni_disegnate`; le quote
    riportano sempre i valori veri di `inputs.b`/`inputs.d`."""
    b, d = inputs.b, inputs.d
    b_dis, d_dis, compresso = _dimensioni_disegnate(b, d)
    nota = NOTA_SCHEMA if compresso else ""
    return Sketch(
        viste=(_vista_direzione1(b_dis, d_dis, b, d, dir1), _vista_direzione2(b_dis, d_dis, b, d, dir2)),
        nota=nota,
    )


def _vista_direzione1(b: float, d: float, b_vero: float, d_vero: float, direzione: DirectionResult) -> Vista:
    """Vento in +y: sopravento il lato y=0 (lungo b), laterali x=0/x=b, sottovento y=d.
    `b`/`d` sono le dimensioni disegnate (eventualmente compresse); `b_vero`/`d_vero` i valori
    reali, riportati nelle quote."""
    fb, fd = _FRAZIONE_ETICHETTA * b, _FRAZIONE_ETICHETTA * d
    bordi: _Bordi = (
        ((fb, 0.0), (0.0, -1.0)),
        ((0.0, fd), (-1.0, 0.0)),
        ((b, fd), (1.0, 0.0)),
        ((fb, d), (0.0, 1.0)),
    )
    freccia = Freccia(coda=(b / 2.0, -_FRAZIONE_FRECCIA * d), punta=(b / 2.0, 0.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b_vero, "m"))
    quota_d = Quota(p1=(0.0, 0.0), p2=(0.0, d), distanza=_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d_vero, "m"))
    return _vista("Pianta — direzione 1", b, d, direzione, bordi, freccia, quota_b, quota_d)


def _vista_direzione2(b: float, d: float, b_vero: float, d_vero: float, direzione: DirectionResult) -> Vista:
    """Vento in +x: sopravento il lato x=0 (lungo d), laterali y=0/y=d, sottovento x=b."""
    fb, fd = _FRAZIONE_ETICHETTA * b, _FRAZIONE_ETICHETTA * d
    bordi: _Bordi = (
        ((0.0, fd), (-1.0, 0.0)),
        ((fb, 0.0), (0.0, -1.0)),
        ((fb, d), (0.0, 1.0)),
        ((b, fd), (1.0, 0.0)),
    )
    freccia = Freccia(coda=(-_FRAZIONE_FRECCIA * b, d / 2.0), punta=(0.0, d / 2.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b_vero, "m"))
    quota_d = Quota(p1=(b, 0.0), p2=(b, d), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d_vero, "m"))
    return _vista("Pianta — direzione 2", b, d, direzione, bordi, freccia, quota_b, quota_d)


def _vista(titolo: str, b: float, d: float, direzione: DirectionResult, bordi: _Bordi,
           freccia: Freccia, quota_b: Quota, quota_d: Quota) -> Vista:
    """Rettangolo b×d + freccia del vento + etichette c_pe sui bordi non 'ND' + le due quote."""
    sopravento, laterale_1, laterale_2, sottovento = bordi
    scostamento = _SCOSTAMENTO_ETICHETTA * max(b, d)
    etichette = (
        _etichetta_faccia(sopravento, scostamento, "c_pe,w", direzione.cpe_windward),
        _etichetta_faccia(laterale_1, scostamento, "c_pe,l", direzione.cpe_side),
        _etichetta_faccia(laterale_2, scostamento, "c_pe,l", direzione.cpe_side),
        _etichetta_faccia(sottovento, scostamento, "c_pe,s", direzione.cpe_leeward),
    )
    forme = (
        Rettangolo(x=0.0, y=0.0, w=b, h=d, stile="calcestruzzo"),
        freccia,
        *(e for e in etichette if e is not None),
        quota_b,
        quota_d,
    )
    return Vista(titolo=titolo, forme=forme)


def _valore(valore: float, decimali: int = 2) -> str:
    """Solo il valore, senza il simbolo (regola 4: `simbolo` è già impostato su `Etichetta`)."""
    return f"{valore:.{decimali}f}".replace(".", ",")


def _etichetta_faccia(bordo: _Bordo, scostamento: float, simbolo: str, valore: float | None) -> Etichetta | None:
    """Etichetta del cpe ancorata sul lato (non al centro, per liberarlo per la freccia/la quota),
    spostata verso l'esterno lungo la normale; None se il coefficiente non è definito (h/d > 5)."""
    if valore is None:
        return None
    ancora, normale = bordo
    punto = (ancora[0] + normale[0] * scostamento, ancora[1] + normale[1] * scostamento)
    return Etichetta(punto=punto, testo=_valore(valore), simbolo=simbolo, ancora="middle")

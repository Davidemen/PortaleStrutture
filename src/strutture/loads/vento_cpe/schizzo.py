"""Live sketch for `vento-cpe-rettangolare`: two Vista, one per wind direction ("Pianta — direzione
1/2"), each the b×d plan rectangle with the windward/side/leeward face labels and dimensions —
docs/ui/WORKBENCH_SPEC.md §7. Pure function of the validated inputs + the computed cpe results; a
failure here must never fail the calculation (guarded in `tool.run`)."""
from strutture.shared.sketch import Etichetta, Freccia, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .models import DirectionResult, VentoCpeInput

_SCOSTAMENTO_ETICHETTA = 0.1  # frazione di max(b,d): distanza delle etichette c_pe fuori dal rettangolo
_MARGINE_QUOTA = 0.15  # frazione di max(b,d): distanza delle linee di quota dal rettangolo
_FRAZIONE_FRECCIA = 0.3  # frazione della dimensione lungo cui soffia il vento: coda della freccia fuori dal rettangolo

_Bordo = tuple[Punto, Punto]  # (punto medio del lato, normale uscente unitaria)
_Bordi = tuple[_Bordo, _Bordo, _Bordo, _Bordo]  # (sopravento, laterale, laterale, sottovento)


def disegna(inputs: VentoCpeInput, dir1: DirectionResult, dir2: DirectionResult) -> Sketch:
    """Due piante b×d, una per direzione del vento, con le facce sopravento/laterali/sottovento."""
    b, d = inputs.b, inputs.d
    return Sketch(viste=(_vista_direzione1(b, d, dir1), _vista_direzione2(b, d, dir2)))


def _vista_direzione1(b: float, d: float, direzione: DirectionResult) -> Vista:
    """Vento in +y: sopravento il lato y=0 (lungo b), laterali x=0/x=b, sottovento y=d."""
    bordi: _Bordi = (
        ((b / 2.0, 0.0), (0.0, -1.0)),
        ((0.0, d / 2.0), (-1.0, 0.0)),
        ((b, d / 2.0), (1.0, 0.0)),
        ((b / 2.0, d), (0.0, 1.0)),
    )
    freccia = Freccia(coda=(b / 2.0, -_FRAZIONE_FRECCIA * d), punta=(b / 2.0, 0.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b, "m"))
    quota_d = Quota(p1=(0.0, 0.0), p2=(0.0, d), distanza=_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d, "m"))
    return _vista("Pianta — direzione 1", b, d, direzione, bordi, freccia, quota_b, quota_d)


def _vista_direzione2(b: float, d: float, direzione: DirectionResult) -> Vista:
    """Vento in +x: sopravento il lato x=0 (lungo d), laterali y=0/y=d, sottovento x=b."""
    bordi: _Bordi = (
        ((0.0, d / 2.0), (-1.0, 0.0)),
        ((b / 2.0, 0.0), (0.0, -1.0)),
        ((b / 2.0, d), (0.0, 1.0)),
        ((b, d / 2.0), (1.0, 0.0)),
    )
    freccia = Freccia(coda=(-_FRAZIONE_FRECCIA * b, d / 2.0), punta=(0.0, d / 2.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b, "m"))
    quota_d = Quota(p1=(b, 0.0), p2=(b, d), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d, "m"))
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


def _etichetta_faccia(bordo: _Bordo, scostamento: float, simbolo: str, valore: float | None) -> Etichetta | None:
    """Etichetta del cpe centrata sul bordo, spostata verso l'esterno lungo la normale; None se il
    coefficiente non è definito (h/d > 5, cfr. `DirectionResult`)."""
    if valore is None:
        return None
    mid, normale = bordo
    punto = (mid[0] + normale[0] * scostamento, mid[1] + normale[1] * scostamento)
    return Etichetta(punto=punto, testo=etichetta_quota(simbolo, valore, "", decimali=2), simbolo=simbolo, ancora="middle")

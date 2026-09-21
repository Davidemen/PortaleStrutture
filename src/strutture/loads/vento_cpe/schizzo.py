"""Live sketch for `vento-cpe-rettangolare`: two Vista, one per wind direction ("Pianta — direzione
1/2"), each the b×d plan rectangle with the windward/side/leeward face labels, the side-wall zones
A/B/C (Circ. C3.3.8.1 fig. C3.3.3) and dimensions — docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION
RULES in shared/sketch.py. Pure function of the validated inputs + the computed cpe results; a
failure here must never fail the calculation (guarded in `tool.run`).

Side walls are split into zones A/B/C at e/5 and e (e = min(crosswind, 2h)) with a tick line at
each limit; since this tool computes a single `cpe_side` for the whole face (no per-zone values),
every zone shows that same value, labelled "A"/"B"/"C" — only on ONE of the two side faces (the
other keeps its division lines, unlabelled: the two faces are symmetric and the 8-text-per-view
budget, rule 4, does not allow labelling both)."""
from strutture.shared.sketch import Etichetta, Freccia, Linea, Punto, Quota, Rettangolo, Sketch, Vista, etichetta_quota

from .models import DirectionResult, VentoCpeInput

_FRAZIONE_ETICHETTA = 0.22  # posizione dell'etichetta lungo il lato (non al centro: libera il centro
# per la freccia del vento e per il testo, centrato, della quota sullo stesso lato — regola 5)
_SCOSTAMENTO_ETICHETTA = 0.09  # frazione di max(b,d): distanza delle etichette c_pe fuori dal rettangolo
_MARGINE_QUOTA = 0.22  # frazione di max(b,d): distanza delle linee di quota dal rettangolo
_FRAZIONE_FRECCIA = 0.4  # frazione della dimensione lungo cui soffia il vento: coda della freccia fuori dal rettangolo
_TICK_ZONA_FRAZIONE = 0.05  # lunghezza dei trattini di confine zona, frazione di max(b,d)

_Bordo = tuple[Punto, Punto]  # (punto di ancoraggio dell'etichetta sul lato, normale uscente unitaria)
_Bordi = tuple[_Bordo, _Bordo]  # (sopravento, sottovento) — le pareti laterali usano `_zone_laterali_*`

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


def _confini_zona_frazione(crosswind_vero_m: float, profondita_vero_m: float, h_vero_m: float) -> tuple[float, float]:
    """(f1, f2): confini delle zone A/B (f1=e/5) e B/C (f2=e), come frazione della profondità
    lungo la parete laterale, e = min(crosswind, 2h) (Circ. C3.3.8.1)."""
    if profondita_vero_m <= 0:
        return 0.0, 0.0
    e_m = min(crosswind_vero_m, 2.0 * h_vero_m)
    return min(e_m / 5.0, profondita_vero_m) / profondita_vero_m, min(e_m, profondita_vero_m) / profondita_vero_m


def disegna(inputs: VentoCpeInput, dir1: DirectionResult, dir2: DirectionResult) -> Sketch:
    """Due piante b×d, una per direzione del vento, con le facce sopravento/laterali/sottovento.
    La geometria usa le dimensioni (eventualmente compresse) di `_dimensioni_disegnate`; le quote
    riportano sempre i valori veri di `inputs.b`/`inputs.d`."""
    b, d, h = inputs.b, inputs.d, inputs.h
    b_dis, d_dis, compresso = _dimensioni_disegnate(b, d)
    nota = NOTA_SCHEMA if compresso else ""
    # direzione 1: crosswind = b (larghezza sopravento), profondità laterale = d; direzione 2: viceversa.
    zone_dir1 = _confini_zona_frazione(b, d, h)
    zone_dir2 = _confini_zona_frazione(d, b, h)
    return Sketch(
        viste=(
            _vista_direzione1(b_dis, d_dis, b, d, dir1, zone_dir1),
            _vista_direzione2(b_dis, d_dis, b, d, dir2, zone_dir2),
        ),
        nota=nota,
    )


def _vista_direzione1(b: float, d: float, b_vero: float, d_vero: float, direzione: DirectionResult,
                       zone: tuple[float, float]) -> Vista:
    """Vento in +y: sopravento il lato y=0 (lungo b), laterali x=0/x=b, sottovento y=d.
    `b`/`d` sono le dimensioni disegnate (eventualmente compresse); `b_vero`/`d_vero` i valori
    reali, riportati nelle quote. Le pareti laterali corrono lungo y (profondità = d)."""
    fb = _FRAZIONE_ETICHETTA * b
    bordi: _Bordi = (
        ((fb, 0.0), (0.0, -1.0)),
        ((fb, d), (0.0, 1.0)),
    )
    freccia = Freccia(coda=(b / 2.0, -_FRAZIONE_FRECCIA * d), punta=(b / 2.0, 0.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b_vero, "m"))
    quota_d = Quota(p1=(0.0, 0.0), p2=(0.0, d), distanza=_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d_vero, "m"))
    zone_forme = _zone_laterali_verticali(0.0, b, d, zone, max(b, d))
    return _vista("Pianta — direzione 1", b, d, direzione, bordi, freccia, quota_b, quota_d, zone_forme)


def _vista_direzione2(b: float, d: float, b_vero: float, d_vero: float, direzione: DirectionResult,
                       zone: tuple[float, float]) -> Vista:
    """Vento in +x: sopravento il lato x=0 (lungo d), laterali y=0/y=d, sottovento x=b.
    Le pareti laterali corrono lungo x (profondità = b)."""
    fd = _FRAZIONE_ETICHETTA * d
    bordi: _Bordi = (
        ((0.0, fd), (-1.0, 0.0)),
        ((b, fd), (1.0, 0.0)),
    )
    freccia = Freccia(coda=(-_FRAZIONE_FRECCIA * b, d / 2.0), punta=(0.0, d / 2.0), stile="carico", testo="vento")
    quota_b = Quota(p1=(0.0, 0.0), p2=(b, 0.0), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("b", b_vero, "m"))
    quota_d = Quota(p1=(b, 0.0), p2=(b, d), distanza=-_MARGINE_QUOTA * max(b, d), testo=etichetta_quota("d", d_vero, "m"))
    zone_forme = _zone_laterali_orizzontali(0.0, d, b, zone, max(b, d))
    return _vista("Pianta — direzione 2", b, d, direzione, bordi, freccia, quota_b, quota_d, zone_forme)


def _valore_con_segno(valore: float, decimali: int = 2) -> str:
    """Valore con il vero segno meno tipografico "−" (non il trattino ASCII) e un "+" esplicito
    per i valori positivi (design review): `simbolo` porta già la lettera/il nome della faccia."""
    numero = f"{abs(valore):.{decimali}f}".replace(".", ",")
    if valore > 0:
        return f"+{numero}"
    if valore < 0:
        return f"−{numero}"
    return numero


def _tick_zona(x0_m: float, y0_m: float, x1_m: float, y1_m: float) -> Linea:
    return Linea(p1=(x0_m, y0_m), p2=(x1_m, y1_m), stile="quota")


_PASSO_ETICHETTA_ZONA_FRAZIONE = 0.5  # scostamento tra etichette di zona impilate, frazione del riferimento (regola 3)


def _zone_laterali_verticali(x0_m: float, x1_m: float, profondita_m: float, zone: tuple[float, float],
                              riferimento_m: float) -> tuple[list[Linea], list[Etichetta]]:
    """Trattini di confine zona su entrambe le pareti laterali VERTICALI (x=x0, x=x1) alle vere
    posizioni geometriche; le etichette A/B/C compaiono solo sulla parete x=x1 (l'altra è
    simmetrica, vedi docstring del modulo) — x1 è il lato libero dalla quota `d`, ancorata su x0.
    Le etichette sono impilate verso l'esterno (non lungo la parete, regola 3): una parete stretta
    altrimenti non avrebbe spazio per 2-3 etichette affiancate."""
    tick_m = _TICK_ZONA_FRAZIONE * riferimento_m
    f1, f2 = zone
    y1_m, y2_m = f1 * profondita_m, f2 * profondita_m
    linee: list[Linea] = []
    for x_m in (x0_m, x1_m):
        if 0.0 < y1_m < profondita_m:
            linee.append(_tick_zona(x_m - tick_m, y1_m, x_m + tick_m, y1_m))
        if y1_m < y2_m < profondita_m:
            linee.append(_tick_zona(x_m - tick_m, y2_m, x_m + tick_m, y2_m))
    passo_m = _PASSO_ETICHETTA_ZONA_FRAZIONE * riferimento_m
    etichette = [
        Etichetta(punto=(x1_m + tick_m * 2.0 + i * passo_m, profondita_m / 2.0), simbolo=lettera, testo="", ancora="middle")
        for i, lettera in enumerate(_lettere_zona(y1_m, y2_m, profondita_m))
    ]
    return linee, etichette


def _zone_laterali_orizzontali(y0_m: float, y1_m: float, profondita_m: float, zone: tuple[float, float],
                                riferimento_m: float) -> tuple[list[Linea], list[Etichetta]]:
    """Come `_zone_laterali_verticali`, per pareti laterali ORIZZONTALI (y=y0, y=y1) — le
    etichette compaiono sulla parete y=y1, libera dalla quota `b`, ancorata su y0."""
    tick_m = _TICK_ZONA_FRAZIONE * riferimento_m
    f1, f2 = zone
    x1_m, x2_m = f1 * profondita_m, f2 * profondita_m
    linee: list[Linea] = []
    for y_m in (y0_m, y1_m):
        if 0.0 < x1_m < profondita_m:
            linee.append(_tick_zona(x1_m, y_m - tick_m, x1_m, y_m + tick_m))
        if x1_m < x2_m < profondita_m:
            linee.append(_tick_zona(x2_m, y_m - tick_m, x2_m, y_m + tick_m))
    passo_m = _PASSO_ETICHETTA_ZONA_FRAZIONE * riferimento_m
    etichette = [
        Etichetta(punto=(profondita_m / 2.0, y1_m + tick_m * 2.0 + i * passo_m), simbolo=lettera, testo="", ancora="middle")
        for i, lettera in enumerate(_lettere_zona(x1_m, x2_m, profondita_m))
    ]
    return linee, etichette


def _lettere_zona(s1_m: float, s2_m: float, profondita_m: float) -> list[str]:
    """Lettere delle zone presenti: A (0..s1) sempre, B (s1..s2) se non degenere, C
    (s2..profondità) se non degenere. Le linee di confine (`_zone_laterali_*`) segnano i veri
    limiti geometrici s1/s2; le ETICHETTE sono impilate verso l'esterno della parete (non lungo di
    essa) nello stesso ordine A, B, C dal filo sopravento a quello sottovento."""
    lettere = ["A"]
    if s2_m > s1_m:
        lettere.append("B")
    if profondita_m > s2_m:
        lettere.append("C")
    return lettere


def _vista(titolo: str, b: float, d: float, direzione: DirectionResult, bordi: _Bordi,
           freccia: Freccia, quota_b: Quota, quota_d: Quota,
           zone_forme: tuple[list[Linea], list[Etichetta]]) -> Vista:
    """Rettangolo b×d + freccia del vento + etichette c_pe sui bordi non 'ND' + zone laterali + quote."""
    sopravento, sottovento = bordi
    scostamento = _SCOSTAMENTO_ETICHETTA * max(b, d)
    etichette = (
        _etichetta_faccia(sopravento, scostamento, "c_pe,w", direzione.cpe_windward),
        _etichetta_faccia(sottovento, scostamento, "c_pe,s", direzione.cpe_leeward),
    )
    linee_zona, etichette_zona = zone_forme
    valore_laterale = _valore_con_segno(direzione.cpe_side) if direzione.cpe_side is not None else None
    etichette_zona_valorizzate = (
        tuple(e.model_copy(update={"testo": valore_laterale}) for e in etichette_zona)
        if valore_laterale is not None else ()
    )
    forme = (
        Rettangolo(x=0.0, y=0.0, w=b, h=d, stile="calcestruzzo"),
        *linee_zona,
        freccia,
        *(e for e in etichette if e is not None),
        *etichette_zona_valorizzate,
        quota_b,
        quota_d,
    )
    return Vista(titolo=titolo, forme=forme)


def _etichetta_faccia(bordo: _Bordo, scostamento: float, simbolo: str, valore: float | None) -> Etichetta | None:
    """Etichetta del cpe ancorata sul lato (non al centro, per liberarlo per la freccia/la quota),
    spostata verso l'esterno lungo la normale; None se il coefficiente non è definito (h/d > 5)."""
    if valore is None:
        return None
    ancora, normale = bordo
    punto = (ancora[0] + normale[0] * scostamento, ancora[1] + normale[1] * scostamento)
    return Etichetta(punto=punto, testo=_valore_con_segno(valore), simbolo=simbolo, ancora="middle")

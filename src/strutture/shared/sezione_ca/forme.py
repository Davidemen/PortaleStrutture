"""Preset outlines and bar layouts (`docs/architecture-phase4.md` §A "Presets"). Outlines are
CCW polygons centred so the origin is a natural reference (centroid for closed/symmetric shapes,
outer corner for L); bar layouts return `tuple[Barra, ...]` in the SAME frame as the matching
outline preset (e.g. `fila_superiore` with `rettangolo`'s centroid-centred frame)."""
from math import cos, pi, sin

from .geometria import Poligono, normalizza_antiorario
from .modelli import Barra


def rettangolo(b_mm: float, h_mm: float) -> Poligono:
    """Rettangolo `b_mm` × `h_mm`, centrato nel baricentro."""
    bx, hy = b_mm / 2.0, h_mm / 2.0
    return normalizza_antiorario(((-bx, -hy), (bx, -hy), (bx, hy), (-bx, hy)))


def cerchio(diametro_mm: float, n_lati: int = 48) -> Poligono:
    """Cerchio di diametro `diametro_mm` come poligono regolare di `n_lati` lati (default 48),
    centrato nell'origine. Il raggio dei vertici è la media fra il raggio nominale (apotema) e
    quello del poligono circoscritto, `R = r/2 * (1 + 1/cos(π/n))`: questa taratura tiene sia
    l'errore di area sia quello d'inerzia sotto lo 0.2 % per n = 48 (un poligono semplicemente
    inscritto sottostima l'area/inerzia di circa lo 0.3-0.6 %)."""
    r = diametro_mm / 2.0
    raggio_vertici = r / 2.0 * (1.0 + 1.0 / cos(pi / n_lati))
    return tuple(
        (raggio_vertici * cos(2.0 * pi * k / n_lati), raggio_vertici * sin(2.0 * pi * k / n_lati))
        for k in range(n_lati)
    )


def sezione_a_t(bf_mm: float, hf_mm: float, bw_mm: float, h_mm: float) -> Poligono:
    """Sezione a T: piattabanda `bf_mm` × `hf_mm` in sommità, anima `bw_mm` larga per l'altezza
    residua; origine nel centro della base dell'anima (y=0 al lembo inferiore)."""
    y_giunzione = h_mm - hf_mm
    contorno = (
        (-bw_mm / 2.0, 0.0), (bw_mm / 2.0, 0.0), (bw_mm / 2.0, y_giunzione),
        (bf_mm / 2.0, y_giunzione), (bf_mm / 2.0, h_mm), (-bf_mm / 2.0, h_mm),
        (-bf_mm / 2.0, y_giunzione), (-bw_mm / 2.0, y_giunzione),
    )
    return normalizza_antiorario(contorno)


def sezione_a_l(bf_mm: float, hf_mm: float, bw_mm: float, h_mm: float) -> Poligono:
    """Sezione a L: ala orizzontale `bf_mm` × `hf_mm` e piedritto verticale `bw_mm` × `h_mm`,
    origine nello spigolo esterno inferiore-sinistro."""
    contorno = (
        (0.0, 0.0), (bf_mm, 0.0), (bf_mm, hf_mm),
        (bw_mm, hf_mm), (bw_mm, h_mm), (0.0, h_mm),
    )
    return normalizza_antiorario(contorno)


def parete_con_elementi_estremita(lw_mm: float, tw_mm: float, le_mm: float, te_mm: float) -> Poligono:
    """Parete di lunghezza `lw_mm` e spessore corrente `tw_mm`, con elementi di estremità lunghi
    `le_mm` (per lato) e spessore `te_mm`; origine nel centro della parete (forma "a osso di
    cane", non convessa)."""
    x1, x4 = -lw_mm / 2.0, lw_mm / 2.0
    x2, x3 = x1 + le_mm, x4 - le_mm
    tw, te = tw_mm / 2.0, te_mm / 2.0
    contorno = (
        (x1, -te), (x2, -te), (x2, -tw), (x3, -tw), (x3, -te), (x4, -te),
        (x4, te), (x3, te), (x3, tw), (x2, tw), (x2, te), (x1, te),
    )
    return normalizza_antiorario(contorno)


def _linspace(a: float, b: float, n: int) -> tuple[float, ...]:
    if n <= 1:
        return ((a + b) / 2.0,)
    passo = (b - a) / (n - 1)
    return tuple(a + i * passo for i in range(n))


def fila_superiore(b_mm: float, h_mm: float, copriferro_mm: float, n_barre: int, diametro_mm: float) -> tuple[Barra, ...]:
    """Fila di `n_barre` barre al lembo superiore di un rettangolo `b_mm` × `h_mm` (frame di
    `rettangolo`), a copriferro netto `copriferro_mm` dal filo di calcestruzzo."""
    y = h_mm / 2.0 - copriferro_mm - diametro_mm / 2.0
    xu = b_mm / 2.0 - copriferro_mm - diametro_mm / 2.0
    return tuple(Barra(x_mm=x, y_mm=y, diametro_mm=diametro_mm) for x in _linspace(-xu, xu, n_barre))


def fila_inferiore(b_mm: float, h_mm: float, copriferro_mm: float, n_barre: int, diametro_mm: float) -> tuple[Barra, ...]:
    """Fila di `n_barre` barre al lembo inferiore — vedi `fila_superiore`."""
    y = -(h_mm / 2.0 - copriferro_mm - diametro_mm / 2.0)
    xu = b_mm / 2.0 - copriferro_mm - diametro_mm / 2.0
    return tuple(Barra(x_mm=x, y_mm=y, diametro_mm=diametro_mm) for x in _linspace(-xu, xu, n_barre))


def perimetrale(b_mm: float, h_mm: float, copriferro_mm: float, n_per_lato: int, diametro_mm: float) -> tuple[Barra, ...]:
    """Armatura perimetrale di un rettangolo `b_mm` × `h_mm`, `n_per_lato` barre per lato
    (spigoli compresi, non duplicati)."""
    xu = b_mm / 2.0 - copriferro_mm - diametro_mm / 2.0
    yu = h_mm / 2.0 - copriferro_mm - diametro_mm / 2.0
    lati = (
        [(x, yu) for x in _linspace(-xu, xu, n_per_lato)],
        [(x, -yu) for x in _linspace(-xu, xu, n_per_lato)],
        [(xu, y) for y in _linspace(-yu, yu, n_per_lato)],
        [(-xu, y) for y in _linspace(-yu, yu, n_per_lato)],
    )
    visti: set[tuple[float, float]] = set()
    punti: list[tuple[float, float]] = []
    for lato in lati:
        for x, y in lato:
            chiave = (round(x, 6), round(y, 6))
            if chiave not in visti:
                visti.add(chiave)
                punti.append((x, y))
    return tuple(Barra(x_mm=x, y_mm=y, diametro_mm=diametro_mm) for x, y in punti)


def circolare(diametro_cerchio_mm: float, copriferro_mm: float, n_barre: int, diametro_barra_mm: float) -> tuple[Barra, ...]:
    """`n_barre` barre equidistanti su una circonferenza (frame di `cerchio`), a copriferro
    netto `copriferro_mm` dal filo di calcestruzzo."""
    r = diametro_cerchio_mm / 2.0 - copriferro_mm - diametro_barra_mm / 2.0
    return tuple(
        Barra(x_mm=r * cos(2.0 * pi * k / n_barre), y_mm=r * sin(2.0 * pi * k / n_barre), diametro_mm=diametro_barra_mm)
        for k in range(n_barre)
    )

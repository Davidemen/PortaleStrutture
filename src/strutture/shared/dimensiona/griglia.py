"""Grid of candidate values for a search: the multiples of `passo` inside [da, a] (WORKBENCH_SPEC
§23.3 point 1), `Decimal` throughout so a 0,05 step never drifts."""
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

MAX_GRADINI = 10_000


class GrigliaError(ValueError):
    """Carries the Italian, user-facing message for an invalid search range."""


def costruisci_griglia(da: float, a: float, passo: float, *, intero: bool) -> tuple[Decimal, ...]:
    """`intero=True` (an integer input field): `passo` must itself be a whole number, and only
    integer multiples of it are offered."""
    if da >= a:
        raise GrigliaError("da deve essere minore di a")
    if passo <= 0:
        raise GrigliaError("Indicare il passo di arrotondamento")
    passo_d = Decimal(str(passo))
    if intero and passo_d != passo_d.to_integral_value():
        raise GrigliaError("Il passo deve essere intero")
    da_d, a_d = Decimal(str(da)), Decimal(str(a))
    primo = (da_d / passo_d).to_integral_value(rounding=ROUND_CEILING)
    ultimo = (a_d / passo_d).to_integral_value(rounding=ROUND_FLOOR)
    conteggio = int(ultimo) - int(primo) + 1
    if conteggio <= 0:
        raise GrigliaError("Nessun multiplo del passo fra da e a")
    if conteggio > MAX_GRADINI:
        raise GrigliaError(f"Troppi valori nell'intervallo: al massimo {MAX_GRADINI}")
    return tuple(passo_d * i for i in range(int(primo), int(ultimo) + 1))


def indici_campionamento(lunghezza: int, punti: int) -> tuple[int, ...]:
    """`punti` grid indices evenly spread over `[0, lunghezza - 1]`, both ends included, fewer when
    the grid itself is smaller (WORKBENCH_SPEC §23.3 point 2 / §24.1)."""
    if lunghezza <= 0:
        return ()
    contati = min(punti, lunghezza)
    if contati <= 1:
        return (0,) if lunghezza else ()
    passo = (lunghezza - 1) / (contati - 1)
    return tuple(sorted({round(i * passo) for i in range(contati)}))

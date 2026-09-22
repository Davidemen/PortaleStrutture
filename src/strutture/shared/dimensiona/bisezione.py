"""Bisection between the bracketing samples, plus the confirmation pass (WORKBENCH_SPEC §23.3
point 4). An `errore` sample hit during bisection is a validity gap invisible to the sampling: it
is treated as the non-admissible side, `affidabile=false`, with the message kept in `motivi`."""
from decimal import Decimal

from .campioni import Campione, EsitoRicerca, Risultato, Sessione, Verso, interrotta

N_CONFERMA = 3


def bisezione(
    campioni: tuple[Campione, ...], indici: tuple[int, ...], griglia: tuple[Decimal, ...],
    verso: Verso, i_lo: int, i_hi: int, limite: bool, sessione: Sessione,
) -> Risultato:
    lo, hi = indici[i_lo], indici[i_hi]
    conosciuti = {i: c for i, c in zip(indici, campioni, strict=True)}
    motivi: list[str] = []
    affidabile = True
    extra: list[Campione] = []
    while hi - lo > 1:
        mid = (lo + hi) // 2
        campione = sessione.prova(griglia[mid])
        if campione is None:
            return interrotta([*campioni, *extra], verso, sessione.valutazioni)
        extra.append(campione)
        conosciuti[mid] = campione
        if campione.esito == "errore":
            affidabile = False
            motivi.append(f"Fra {griglia[lo]} e {griglia[hi]} il metodo non è applicabile: {campione.messaggio}")
            lo, hi = (mid, hi) if verso == "minimo" else (lo, mid)
            continue
        ammissibile_da_basso = (campione.esito == "ammissibile") == (verso == "minimo")
        lo, hi = (lo, mid) if ammissibile_da_basso else (mid, hi)
    indice_risposta = hi if verso == "minimo" else lo
    valore = griglia[indice_risposta]
    if conosciuti[indice_risposta].avviso_nuovo:
        affidabile = False
        motivi.append(conosciuti[indice_risposta].avviso_nuovo)
    affidabile_conferma, motivi_conferma, conferma = _conferma(griglia, indice_risposta, verso, sessione)
    esito: EsitoRicerca = "limite_validita" if limite else "trovato"
    tutti_motivi = tuple(motivi + motivi_conferma) or (("Il valore trovato è il limite di validità del metodo",) if limite else ())
    return Risultato(
        esito=esito, verso=verso, valore=valore, affidabile=affidabile and affidabile_conferma and not limite,
        motivi=tutti_motivi, campioni=(*campioni, *extra, *conferma), valutazioni=sessione.valutazioni,
    )


def _conferma(
    griglia: tuple[Decimal, ...], indice_risposta: int, verso: Verso, sessione: Sessione,
) -> tuple[bool, list[str], list[Campione]]:
    """The next N_CONFERMA grid values beyond the answer, towards the safer side."""
    passo = 1 if verso == "minimo" else -1
    affidabile = True
    motivi: list[str] = []
    campioni: list[Campione] = []
    for i in range(1, N_CONFERMA + 1):
        indice = indice_risposta + passo * i
        if not (0 <= indice < len(griglia)):
            break
        campione = sessione.prova(griglia[indice])
        if campione is None:
            break
        campioni.append(campione)
        if campione.esito != "ammissibile":
            affidabile = False
            motivi.append(f"Il valore {griglia[indice]}, subito oltre la risposta, non soddisfa le verifiche")
        if campione.avviso_nuovo:
            affidabile = False
            motivi.append(campione.avviso_nuovo)
    return affidabile, motivi, campioni

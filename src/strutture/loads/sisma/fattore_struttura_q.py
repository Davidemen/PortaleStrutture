"""NTC 2018 §7.3.1 — fattore di struttura orizzontale q (Sisma!I41)."""


def fattore_struttura_q(q0: float, kr: float, *, is_uls: bool) -> float:
    """q = q0·KR per gli stati limite ultimi (SLV/SLC); q = 1 per gli stati limite di esercizio
    (SLO/SLD), dove lo spettro elastico si usa senza riduzione."""
    return q0 * kr if is_uls else 1.0

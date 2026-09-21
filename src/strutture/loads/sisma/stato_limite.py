"""Sisma!N25: `=IF(I25="slv","slu",IF(I25="slc","slu","sle"))` — classifies a limit state as
ultimate (SLV/SLC, divides the elastic spectrum by q) or serviceability (SLO/SLD, uses it as-is).

Excel's text comparison is case-insensitive, so `I25="slv"` matches the uppercase dropdown value
"SLV" without any special handling — this is not a bug (see `docs/specs/sisma.md` §7 item 5), but a
case-sensitive language needs an explicit normalization to reproduce the same behaviour.
"""

STATI_LIMITE_ULTIMI = frozenset({"SLV", "SLC"})


def is_stato_limite_uls(stato_limite: str) -> bool:
    """True for SLV/SLC (Stati Limite Ultimi), False for SLO/SLD (Stati Limite di Esercizio)."""
    return stato_limite.strip().upper() in STATI_LIMITE_ULTIMI

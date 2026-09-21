"""Case- and accent-insensitive text normalisation used to key the Comuni lookup indices."""
import unicodedata


def normalize_name(value: str) -> str:
    """Fold accents and case so "Città Sant'Angelo" == "citta sant'angelo" == "CITTA' SANT ANGELO"."""
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value).__name__}")
    decomposed = unicodedata.normalize("NFKD", value.strip())
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_accents.casefold()

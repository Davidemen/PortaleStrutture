"""Presentation metadata that belongs to the UI, not to the calculation packages: the short code
(sigla) shown on navigation chips. Central on purpose: uniqueness is checked in one place and the
codes can be tuned without touching thirty tool packages."""

SIGLE: dict[str, str] = {
    "neve-carico-falda": "NEV", "neve-accumulo": "NAC",
    "sisma-vita-riferimento": "SVR", "sisma-parametri-sito": "SPS", "sisma-fattori-struttura": "SFS",
    "sisma-spettro": "SSP", "sisma-completo": "SIS",
    "vento-pressione": "VEN", "vento-cpe-rettangolare": "CPE",
    "ca-trave-rettangolare": "TRV", "ca-taglio-non-armato": "TNA",
    "ca-pilastro-rettangolare": "PIR", "ca-pilastro-circolare": "PIC", "ca-mensola-tozza": "MEN",
    "ca-sle-limitazione-tensioni": "SLE", "ca-apertura-fessure": "FES",
    "ca-apertura-fessure-semplificata": "FSS", "ca-punzonamento": "PUN",
    "ca-sezione-dominio-mn": "SMN",
    "acciaio-colonna-h-ec3": "COL", "acciaio-sezione-h-rimpiattata": "SHR",
    "acciaio-resistenza-incendio": "INC", "acciaio-proprieta-temperatura": "TMP",
    "geo-cedimento-edometrico": "EDO", "geo-cedimento-elastico-newmark": "NEW",
    "geo-cedimento-elastico-timoshenko-goodier": "TG", "muro-sostegno": "MUR",
    "fond-plinto-isolato": "PLI", "fond-plinto-su-pali": "PLP",
    "fond-trave-collegamento": "TCO", "fond-pavimento-industriale": "PAV",
}
MAX_SIGLA = 3


def sigla_for(tool_name: str, title: str) -> str:
    """The tool's navigation code; tools without an entry fall back to the first letters of the title."""
    fallback = "".join(ch for ch in title if ch.isalpha())[:2].upper() or "?"
    return SIGLE.get(tool_name, fallback)

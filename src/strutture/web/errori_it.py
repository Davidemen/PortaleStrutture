"""Translate a pydantic v2 `ValidationError.errors()` entry into an Italian, user-facing message
(WORKBENCH_SPEC §23.4/§26.2: every 422 in Italian). A model's own `field_validator`/`model_validator`
`ValueError` is already Italian (that text passes straight through, `"Value error, "` stripped) --
this module only covers pydantic's OWN built-in constraint violations (`gt`/`le`/`min_length`/
`extra_forbidden`/...), which come back in English otherwise. Best-effort: an unrecognised `type`
falls back to pydantic's own message rather than raising, so a 422 is never itself a 500."""
from decimal import Decimal
from typing import Any

from strutture.shared.dimensiona.serie import MAX_PUNTI

# Exact wording the spec calls out for these fields, regardless of which single bound pydantic
# happened to report (`greater_than` for 0, `less_than_equal` for the top) -- one sentence stating
# the whole rule reads better than two different one-sided messages for the same field.
_MESSAGGI_COMPLETI: dict[str, str] = {
    "obiettivo_sfruttamento": "L'obiettivo di sfruttamento deve essere maggiore di 0 e al massimo 1,00",
    "obiettivo": "L'obiettivo deve essere maggiore di 0 e al massimo 1,00",
    "punti": f"Indicare fra 2 e {MAX_PUNTI} punti",
}
_MESSAGGI_MANCANTE: dict[str, str] = {
    "passo": "Indicare il passo di arrotondamento",
}

_ETICHETTE: dict[str, str] = {
    "obiettivo_sfruttamento": "l'obiettivo di sfruttamento",
    "obiettivo_su_verifiche_minimo": "l'obiettivo sulle verifiche di minimo",
    "passi_per_tipo": "il passo per tipo",
    "passi_per_campo": "l'eccezione",
    "passo": "il passo",
    "strumento": "lo strumento",
    "campo": "il campo",
    "revisione": "la revisione",
    "sigla": "la sigla",
    "inputs": "i dati",
    "da": "il valore «da»",
    "a": "il valore «a»",
    "obiettivo": "l'obiettivo",
    "punti": "il numero di punti",
    "verso": "il verso",
}


def messaggio_errore_it(errore: dict[str, Any]) -> str:
    loc = tuple(errore.get("loc", ()))
    ultimo = str(loc[-1]) if loc else ""
    campo = _ultimo_nome(loc)
    if campo in _MESSAGGI_COMPLETI:
        return _MESSAGGI_COMPLETI[campo]
    etichetta = _ETICHETTE.get(campo, ultimo or "il campo")
    tipo = errore.get("type", "")
    ctx = errore.get("ctx", {})
    if tipo == "missing":
        return _MESSAGGI_MANCANTE.get(campo, f"Indicare {etichetta}")
    if tipo == "greater_than":
        return f"{_maiuscola(etichetta)} deve essere maggiore di {_numero_it(ctx.get('gt'))}"
    if tipo == "greater_than_equal":
        return f"{_maiuscola(etichetta)} deve essere almeno {_numero_it(ctx.get('ge'))}"
    if tipo == "less_than":
        return f"{_maiuscola(etichetta)} deve essere minore di {_numero_it(ctx.get('lt'))}"
    if tipo == "less_than_equal":
        return f"{_maiuscola(etichetta)} deve essere al massimo {_numero_it(ctx.get('le'))}"
    if tipo == "string_too_short":
        minimo = ctx.get("min_length")
        if minimo == 1:
            vuoto = "vuota" if etichetta.startswith("la ") else "vuoto"
            return f"{_maiuscola(etichetta)} non può essere {vuoto}"
        return f"{_maiuscola(etichetta)} troppo corto (minimo {minimo} caratteri)"
    if tipo == "string_too_long":
        return f"{_maiuscola(etichetta)} troppo lungo (massimo {ctx.get('max_length')} caratteri)"
    if tipo == "too_short":
        return f"{_maiuscola(etichetta)}: indicare almeno {ctx.get('min_length', ctx.get('field_type', ''))} valori"
    if tipo == "too_long":
        return f"{_maiuscola(etichetta)}: al massimo {ctx.get('max_length')} valori"
    if tipo == "extra_forbidden":
        return f"Campo non riconosciuto: {'.'.join(str(p) for p in loc)}"
    if tipo in ("int_parsing", "int_type"):
        return f"{_maiuscola(etichetta)} deve essere un numero intero"
    if tipo in ("float_parsing", "float_type", "decimal_parsing"):
        return f"{_maiuscola(etichetta)} deve essere un numero"
    if tipo == "bool_parsing" or tipo == "bool_type":
        return f"{_maiuscola(etichetta)} deve essere sì o no"
    if tipo == "literal_error":
        attesi = ", ".join(str(v) for v in ctx.get("expected", "").split(" or ")) if ctx.get("expected") else ""
        return f"{_maiuscola(etichetta)} non riconosciuto" + (f" (valori ammessi: {attesi})" if attesi else "")
    if tipo == "dict_type":
        return f"{_maiuscola(etichetta)} deve essere un oggetto"
    return str(errore.get("msg", "")).removeprefix("Value error, ")


def _ultimo_nome(loc: tuple) -> str:
    for parte in reversed(loc):
        if isinstance(parte, str):
            return parte
    return ""


def _maiuscola(testo: str) -> str:
    return testo[0].upper() + testo[1:] if testo else testo


def _numero_it(valore: Any) -> str:
    if valore is None:
        return ""
    try:
        return format(Decimal(str(valore)).normalize(), "f").replace(".", ",")
    except Exception:  # noqa: BLE001 - formatting is a nicety, never worth a 500
        return str(valore)

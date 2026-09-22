"""Resolve the proposed rounding step for one field (§26.5): exception > type step > integer > none."""
from decimal import Decimal
from typing import Any, Literal, NamedTuple

from strutture.shared import units

from .modelli import Impostazioni, TipoDato

Origine = Literal["campo", "tipo", "intero"]
_UNITA_DEL_TIPO: dict[TipoDato, str] = {
    "lunghezza_m": "m", "lunghezza_cm": "cm", "lunghezza_mm": "mm",
    "diametro_armatura": "mm", "passo_armatura": "mm", "copriferro": "mm", "spessore": "mm",
}
_DECIMALI_PASSO = 4


class PassoProposto(NamedTuple):
    passo: float | None
    origine: Origine | None
    tipo: TipoDato | None


def passo_proposto(
    impostazioni: Impostazioni, strumento: str, campo: str, schema_campo: dict[str, Any], tipo: TipoDato | None
) -> PassoProposto:
    eccezione = _eccezione(impostazioni, strumento, campo)
    if eccezione is not None:
        return PassoProposto(eccezione.passo, "campo", tipo)
    if tipo is None:
        return PassoProposto(None, None, None)
    passo_tipo = impostazioni.passi_per_tipo.get(tipo)
    if passo_tipo is not None:
        return PassoProposto(_converti(passo_tipo, tipo, schema_campo.get("unit")), "tipo", tipo)
    if tipo == "intero":
        return PassoProposto(1.0, "intero", tipo)
    return PassoProposto(None, None, tipo)


def _eccezione(impostazioni: Impostazioni, strumento: str, campo: str):
    for candidata in impostazioni.passi_per_campo:
        if candidata.strumento == strumento and candidata.campo == campo:
            return candidata
    return None


def _converti(passo: float, tipo: TipoDato, unita_campo: str | None) -> float:
    """Convert a type step (in the type's own unit) into the field's unit; refuse a result that
    does not survive the 4-decimal rule (§26.3)."""
    unita_tipo = _UNITA_DEL_TIPO.get(tipo)
    if unita_tipo is None or unita_campo is None or unita_campo == unita_tipo:
        return passo
    convertito = _CONVERSIONI.get((unita_tipo, unita_campo), lambda v: v)(passo)
    if _decimali(convertito) > _DECIMALI_PASSO:
        raise ValueError(
            f"Il passo di {_numero_it(passo)} {unita_tipo} non è esprimibile in {unita_campo} per il campo"
        )
    return convertito


_CONVERSIONI = {
    ("m", "cm"): units.m_to_cm, ("m", "mm"): units.m_to_mm,
    ("cm", "m"): units.cm_to_m, ("cm", "mm"): units.cm_to_mm,
    ("mm", "m"): units.mm_to_m, ("mm", "cm"): units.mm_to_cm,
}


def _decimali(valore: float) -> int:
    testo = format(Decimal(str(valore)).normalize(), "f")
    return len(testo.split(".", 1)[1]) if "." in testo else 0


def _numero_it(valore: float) -> str:
    return format(Decimal(str(valore)).normalize(), "f").replace(".", ",")

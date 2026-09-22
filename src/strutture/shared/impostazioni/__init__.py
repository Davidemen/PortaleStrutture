"""Office-wide settings (WORKBENCH_SPEC.md §26): one set of defaults for the whole installation,
proposed (never imposed) to the "Dimensiona" (§23) and "Sensibilità" (§24) dialogs."""
from .modelli import FABBRICA, MAX_ECCEZIONI, PASSO_MAX, Impostazioni, ImpostazioniSalvate, PassoCampo, TipoDato
from .risolvi import PassoProposto, passo_proposto
from .tipi_dato import tipo_dato
from .validazione import valida_eccezioni

__all__ = [
    "FABBRICA",
    "MAX_ECCEZIONI",
    "PASSO_MAX",
    "Impostazioni",
    "ImpostazioniSalvate",
    "PassoCampo",
    "PassoProposto",
    "TipoDato",
    "passo_proposto",
    "tipo_dato",
    "valida_eccezioni",
]

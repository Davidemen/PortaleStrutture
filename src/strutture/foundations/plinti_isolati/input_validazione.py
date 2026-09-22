"""Cross-field validation for `PlintoIsolatoInput`, factored out of `input.py` to keep both modules
within the size limits (docs/BUILD_CONTRACT.md, regola 12). Same rules, same error messages."""
from typing import TYPE_CHECKING

from strutture.shared.load_table import validate_unique_nodo_combo

from .rows import validate_unique_famiglia

if TYPE_CHECKING:
    from .input import PlintoIsolatoInput

_CAMPI_BLOCCO_TERRENO = (
    "terreno_phi_k_deg", "terreno_c_k_kpa", "terreno_cu_k_kpa", "terreno_gamma_kn_m3", "terreno_profondita_falda_m",
)


def valida(modello: "PlintoIsolatoInput") -> None:
    """Reazioni/resistenze uniche per famiglia + coerenza del blocco opzionale 'Terreno'."""
    validate_unique_nodo_combo(modello.reazioni)
    validate_unique_famiglia(modello.resistenze)
    famiglie_reazioni = {row.famiglia for row in modello.reazioni}
    if None in famiglie_reazioni:
        raise ValueError("ogni riga della tabella reazioni deve specificare una famiglia")
    famiglie_resistenze = {row.famiglia for row in modello.resistenze}
    mancanti = famiglie_reazioni - famiglie_resistenze
    if mancanti:
        raise ValueError(f"manca la resistenza di progetto del terreno per le famiglie: {sorted(mancanti)}")
    _valida_blocco_terreno(modello)


def _valida_blocco_terreno(modello: "PlintoIsolatoInput") -> None:
    """Il blocco 'Terreno' è opzionale (`terreno_condizione` assente = non compilato); quando è
    compilato, i parametri richiesti dalla condizione di drenaggio scelta sono obbligatori.

    HIGH finding: un blocco compilato a metà nel verso opposto (parametri valorizzati ma
    `terreno_condizione` non selezionata) veniva prima saltato in silenzio da entrambi i rami
    (`if self.terreno_condizione is None: return`): la verifica di capacità portante restava
    vuota (`capacita_portante.righe == ()`, nessun avviso) e l'utente credeva di averla
    attivata. Qui viene invece rifiutato esplicitamente."""
    campi_valorizzati = tuple(
        nome for nome in _CAMPI_BLOCCO_TERRENO if getattr(modello, nome) is not None
    )
    if modello.terreno_condizione is None:
        if campi_valorizzati:
            raise ValueError(
                "blocco 'Terreno': selezionare la condizione di drenaggio (terreno_condizione) "
                "per attivare la verifica di capacità portante, oppure svuotare i campi "
                f"{', '.join(campi_valorizzati)}"
            )
        return
    if modello.terreno_gamma_kn_m3 is None:
        raise ValueError("terreno_gamma_kn_m3 è obbligatorio quando il blocco Terreno è compilato")
    if modello.terreno_condizione == "drenata" and (
        modello.terreno_phi_k_deg is None or modello.terreno_c_k_kpa is None
    ):
        raise ValueError("terreno_phi_k_deg e terreno_c_k_kpa sono obbligatori in condizione drenata")
    if modello.terreno_condizione == "non_drenata" and modello.terreno_cu_k_kpa is None:
        raise ValueError("terreno_cu_k_kpa è obbligatorio in condizione non drenata")

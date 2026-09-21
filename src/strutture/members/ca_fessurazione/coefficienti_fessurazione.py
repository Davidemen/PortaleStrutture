"""Table lookups for `ca-apertura-fessure` (Circ. 2019 §C4.1.6-C4.1.9), calc steps 5-7 and 14."""
from strutture.shared.tables import exact_lookup

from .tables import (
    K1_PER_TIPO_BARRE,
    K2_PER_SOLLECITAZIONE,
    KT_PER_DURATA_CARICO,
    WLIM_MM_PER_CLASSE,
    ClasseFessurazione,
    DurataCarico,
    TipoBarre,
    TipoSollecitazione,
)


def k1_per_tipo_barre(tipo_barre: TipoBarre) -> float:
    """k1 = VLOOKUP(tipo_barre, S5:T6) [E39], §C4.1.7."""
    return exact_lookup(K1_PER_TIPO_BARRE, tipo_barre)


def k2_per_sollecitazione(tipo_sollecitazione: TipoSollecitazione) -> float:
    """k2 = VLOOKUP(tipo_sollecitazione, V5:W6) [E40], §C4.1.9."""
    return exact_lookup(K2_PER_SOLLECITAZIONE, tipo_sollecitazione)


def kt_per_durata_carico(durata_carico: DurataCarico) -> float:
    """kt = VLOOKUP(durata_carico, P5:Q6) [E43], §C4.1.6."""
    return exact_lookup(KT_PER_DURATA_CARICO, durata_carico)


def wlim_mm_per_classe(classe_fessurazione: ClasseFessurazione) -> float:
    """wlim = VLOOKUP(classe_fessurazione, Y5:Z7) [E46]."""
    return exact_lookup(WLIM_MM_PER_CLASSE, classe_fessurazione)

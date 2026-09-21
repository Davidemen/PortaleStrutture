"""Step: pick the governing row of the `azioni` table (docs/BUILD_CONTRACT.md "Batch 2" many-rows
result contract: `governante` is the expanded governing row). A row with `rapporto=None` (N_Ed outside
the resistance domain) is a worse outcome than any finite ratio, so it always wins the envelope."""
from .models_output import RigaAzione

_RAPPORTO_FUORI_DOMINIO = float("inf")  # internal ranking key only, never stored in a response field.


def _chiave(riga: RigaAzione) -> float:
    return _RAPPORTO_FUORI_DOMINIO if riga.rapporto is None else riga.rapporto


def riga_governante(righe: tuple[RigaAzione, ...]) -> RigaAzione:
    return max(righe, key=_chiave)


def indice_governante(righe: tuple[RigaAzione, ...]) -> int:
    """Indice della riga governante in `righe` (stesso criterio di `riga_governante`): serve a
    `compose.py` per sostituire quella riga con la sua rifinitura esatta (`capacita.riga_azione_esatta`)."""
    return max(range(len(righe)), key=lambda i: _chiave(righe[i]))

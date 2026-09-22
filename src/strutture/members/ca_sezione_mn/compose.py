"""Composes the ca-sezione-dominio-mn steps into a Report. `run` only composes the step modules
(docs/BUILD_CONTRACT.md "Modularity"); each step lives in its own small module. No `legacy_compat`
mode (docs/architecture-phase4.md: "No spreadsheet exists ... no legacy_compat mode")."""
import logging

from strutture.shared.report import Report, success
from strutture.shared.sezione_ca.domini import dominio_nm, intervallo_n
from strutture.shared.sezione_ca.geometria import bounding_box
from strutture.shared.sezione_ca.modelli import Sezione

from .assi_neutri import asse_neutro
from .capacita import riga_azione, riga_azione_esatta
from .checks import check_pressoflessione
from .geometria_riepilogo import riepilogo_geometrico
from .governante import indice_governante
from .models_input import SezioneMnInput
from .models_output import ResistenzeGovernante, RigaAzione, SezioneMnOutput
from .rows import AzioneRow
from .schizzo import disegna as disegna_schizzo
from .sezione_builder import costruisci_sezione

logger = logging.getLogger(__name__)

# n_punti per dominio_nm: il default 72 (36/ramo) dà un errore di interpolazione medio ~2.8% (fino
# a ~10% in punti isolati vicino a una transizione pivot: l'errore non scende regolarmente con la
# risoluzione perché la curva ha spigoli lì — finding ALTO interpolazione.py, misurato). Alzarlo a
# 120 (60/ramo) porta l'errore medio a ~2.2%, il massimo consentito dal budget di reattività della
# UI live (docs/BUILD_CONTRACT.md: < 300 ms per l'esempio del tool, verificato anche sotto
# strumentazione di coverage): oltre questo valore il budget viene superato. Questo riduce ma non
# elimina l'errore sulle righe NON governanti; la riga governante — l'unica su cui si basano check
# ed esito — viene invece SEMPRE rifinita a M_Rd esatto (`capacita.riga_azione_esatta`),
# indipendentemente da `n_punti`.
N_PUNTI_DOMINIO = 120


def _dimensioni_flessionali(sezione: Sezione) -> tuple[float, float]:
    """`(h_x_mm, h_y_mm)`: ingombro della sezione lungo y (per la flessione attorno a x) e lungo x
    (per la flessione attorno a y), per l'eccentricità minima EN1992-1-1 §6.1(4) (`rapporto.py`)."""
    xmin, ymin, xmax, ymax = bounding_box(sezione.contorno)
    return ymax - ymin, xmax - xmin


def _con_governante_esatta(
    righe: tuple[RigaAzione, ...], azioni: tuple[AzioneRow, ...], sezione: Sezione,
    h_x_mm: float, h_y_mm: float, n_rd_kN: float,
) -> tuple[tuple[RigaAzione, ...], RigaAzione, ResistenzeGovernante | None]:
    """Sostituisce, nella tabella e come riga governante, la riga individuata come governante dalla
    lettura interpolata con la sua versione a M_Rd esatto (vedi `capacita.riga_azione_esatta`)."""
    idx = indice_governante(righe)
    governante, resistenze = riga_azione_esatta(azioni[idx], sezione, h_x_mm, h_y_mm, n_rd_kN)
    return righe[:idx] + (governante,) + righe[idx + 1:], governante, resistenze


def run(inputs: SezioneMnInput) -> Report[SezioneMnOutput]:
    sezione = costruisci_sezione(inputs)
    geometria = riepilogo_geometrico(sezione)
    dominio_x = dominio_nm(sezione, "x", n_punti=N_PUNTI_DOMINIO)
    dominio_y = dominio_nm(sezione, "y", n_punti=N_PUNTI_DOMINIO)
    h_x_mm, h_y_mm = _dimensioni_flessionali(sezione)
    n_rd_kN = intervallo_n(sezione)[1]

    righe_interpolate = tuple(
        riga_azione(azione, dominio_x, dominio_y, h_x_mm, h_y_mm, n_rd_kN) for azione in inputs.azioni
    )
    righe, governante, resistenze = _con_governante_esatta(righe_interpolate, inputs.azioni, sezione, h_x_mm, h_y_mm, n_rd_kN)
    check = check_pressoflessione(governante)

    try:
        piano_asse_neutro = asse_neutro(sezione, governante)
        schizzo = disegna_schizzo(sezione, piano_asse_neutro)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per ca-sezione-dominio-mn")
        schizzo = None

    data = SezioneMnOutput(
        geometria=geometria,
        materiali=sezione.materiali,
        dominio_x=dominio_x,
        dominio_y=dominio_y,
        righe=righe,
        governante=governante,
        resistenze_governante=resistenze,
        schizzo=schizzo,
    )
    return success(data, inputs, checks=(check,))

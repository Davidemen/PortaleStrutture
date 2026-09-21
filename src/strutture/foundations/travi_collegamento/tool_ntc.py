"""Composes the NTC2018 branch of `fond-trave-collegamento` (sheet `Travi collegamento NTC2018`)."""
import logging

from strutture.shared.report import Report, success
from strutture.shared.sketch import Sketch

from .azione import azione
from .compressione import compressione
from .materiali import materiali
from .minimi_ntc import minimi_ntc
from .models import TraviCollegamentoInput
from .output import TraviCollegamentoOutput
from .schizzo import disegna as disegna_schizzo
from .sismica_ntc import sismica_ntc
from .snellezza_ntc import snellezza_ntc
from .trazione import trazione

logger = logging.getLogger(__name__)


def run_ntc(inputs: TraviCollegamentoInput) -> Report[TraviCollegamentoOutput]:
    assert inputs.f0 is not None and inputs.categoria_topografica is not None  # enforced by the input validator
    sismica = sismica_ntc(inputs.categoria_sottosuolo, inputs.categoria_topografica, inputs.f0, inputs.ag_g)
    mat = materiali(
        inputs.b_mm, inputs.h_mm, inputs.phi_mm, inputs.n_barre,
        inputs.classe_calcestruzzo, inputs.classe_acciaio, legacy_compat=inputs.legacy_compat,
    )
    az = azione(inputs.n1_kN, inputs.n2_kN, sismica.amax_g, sismica.alpha)
    comp = compressione(mat.ac_mm2, mat.fcd_MPa, az.ned_kN)
    traz = trazione(mat.as_mm2, mat.fyd_MPa, az.ned_kN, comp.tasso_lavoro, legacy_compat=inputs.legacy_compat)
    snel = snellezza_ntc(inputs.b_mm, inputs.h_mm, inputs.l_mm, inputs.beta, az.ned_kN, mat.ac_mm2, mat.fcd_MPa)
    min_ = minimi_ntc(inputs.b_mm, inputs.h_mm, inputs.cf_mm, inputs.phi_staffa_mm, inputs.n_bracci, inputs.p_mm)
    schizzo: Sketch | None
    try:
        schizzo = disegna_schizzo(inputs)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per fond-trave-collegamento (NTC2018)")
        schizzo = None
    data = TraviCollegamentoOutput(
        sismica_ntc=sismica, azione=az, materiali=mat, compressione=comp, trazione=traz,
        snellezza_ntc=snel, minimi_ntc=min_, schizzo=schizzo,
    )
    checks = (comp.verifica, traz.verifica, snel.verifica, min_.verifica)
    return success(data, inputs, checks=checks)

"""Step: per-row verification, family envelopes and reinforcement/SLS design for one footing,
factored out of `tool.py` to keep both modules within the size limits (docs/BUILD_CONTRACT.md,
regola 12). `run()` (in `tool.py`) composes `calcola()`'s result into checks/output/sketch."""
from typing import NamedTuple

from strutture.shared.load_table import governing

from .capacita_portante import CapacitaPortanteOutput, capacita_portante
from .flessione import flessione
from .input import PlintoIsolatoInput
from .inviluppo import Eccentricita, InviluppoRiga, eccentricita_globale, inviluppo
from .materiali import Materiali, materiali
from .models_flessione import Flessione
from .models_sle import Sle
from .riga_verifica import RigaVerifica, riga_verifica
from .sle import sle


class Calcolo(NamedTuple):
    """Intermediate results shared by the checks, the output model and the sketch."""

    righe: tuple[RigaVerifica, ...]
    inviluppo_righe: tuple[InviluppoRiga, ...]
    eccentricita: Eccentricita
    materiali_result: Materiali
    flessione_result: Flessione
    sle_result: Sle
    capacita_portante_result: CapacitaPortanteOutput
    avvisi_capacita_portante: tuple[str, ...]
    riga_governante: RigaVerifica


def calcola(inputs: PlintoIsolatoInput) -> Calcolo:
    """Per-row verification, family envelopes and reinforcement/SLS design for one footing."""
    righe: tuple[RigaVerifica, ...] = tuple(
        riga_verifica(
            row, inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.h_interro_m,
            inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.h_pedestal_sopra_m, inputs.h_pedestal_sotto_m,
            inputs.offset_leva_m, inputs.ex_m, inputs.ey_m, inputs.gamma_terreno_kNm3, inputs.phi_terreno_deg,
            metodo_pressioni=inputs.metodo_pressioni, legacy_compat=inputs.legacy_compat,
        )
        for row in inputs.reazioni
    )
    inviluppo_righe = inviluppo(righe)
    materiali_result = materiali(inputs.classe_calcestruzzo, inputs.grado_acciaio, inputs.gamma_s,
                                  legacy_compat=inputs.legacy_compat)
    flessione_result = flessione(
        inviluppo_righe, inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.a_pedestal_m, inputs.b_pedestal_m,
        inputs.ex_m, inputs.ey_m, inputs.copriferro_cm, inputs.passo_armatura_cm,
        inputs.diametro_manuale_x_mm, inputs.diametro_manuale_y_mm,
        materiali_result.acciaio.fyd_MPa, materiali_result.acciaio.fyk_MPa, materiali_result.calcestruzzo.fctm_MPa,
        legacy_compat=inputs.legacy_compat,
    )
    sle_result = sle(inviluppo_righe, flessione_result, inputs.ax_m, inputs.by_m, inputs.h_plinto_m,
                      inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.ex_m, inputs.ey_m,
                      copriferro_cm=inputs.copriferro_cm, legacy_compat=inputs.legacy_compat)
    capacita_portante_result, avvisi_capacita_portante = capacita_portante(righe, inputs)

    governante = governing(righe, lambda r: r.sigma_max_kpa, "max")  # type: ignore[arg-type]
    if governante is None:
        raise ValueError("la tabella reazioni non puo' essere vuota")

    return Calcolo(
        righe=righe, inviluppo_righe=inviluppo_righe, eccentricita=eccentricita_globale(righe),
        materiali_result=materiali_result, flessione_result=flessione_result, sle_result=sle_result,
        capacita_portante_result=capacita_portante_result, avvisi_capacita_portante=avvisi_capacita_portante,
        riga_governante=righe[governante.indice],
    )

"""Tool registration: acciaio-sezione-h-rimpiattata — H/I profile reinforced with welded plates.

One composed `Tool`. Section-property steps (baricentro, inerzia, plastico, moduli_elastici,
raggi) stay small pure functions over the plain `Elemento` geometry built by `elementi.py`; `run`
only wires them together (rows 16-50 of the sheet, an unrelated EC3 member check, are not ported —
architecture-batch2.md §1).
"""
import logging

from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .baricentro import area_totale_mm2, baricentro
from .elementi import ALTEZZA_ANIMA_RIFERIMENTO_LEGACY_MM, costruisci_elementi, elementi_profilo
from .inerzia import contributo_ix_mm4, contributo_iy_mm4, inerzia_sezione_mm4
from .models import SezioneHRimpiattataInput
from .moduli_elastici import wel_mm3
from .plastico import wpl_x_legacy_mm3, wpl_x_mm3, wpl_y_legacy_mm3, wpl_y_mm3
from .raggi import raggio_giro_mm
from .risultati import MM3_PER_CM3, MM4_PER_CM4, ElementoRisultato, Sezione, SezioneHRimpiattataOutput
from .schizzo import disegna as disegna_schizzo

logger = logging.getLogger(__name__)

ESEMPIO_AUREO = {
    "h_profilo_mm": 114, "b_profilo_mm": 120, "tf_mm": 8, "tw_mm": 5,
    "piatti": [{"b_mm": 8, "h_mm": 105}, {"b_mm": 0, "h_mm": 105}],
}


def _riga_elemento(elemento, x_n_mm: float, y_n_mm: float) -> ElementoRisultato:
    delta_x, delta_y = abs(elemento.x_mm - x_n_mm), abs(elemento.y_mm - y_n_mm)
    return ElementoRisultato(
        nome=elemento.nome, area_mm2=elemento.area_mm2, x_mm=elemento.x_mm, y_mm=elemento.y_mm,
        delta_x_mm=delta_x, delta_y_mm=delta_y,
        wpl_x_i_cm3=elemento.area_mm2 * delta_y / MM3_PER_CM3,
        wpl_y_i_cm3=elemento.area_mm2 * delta_x / MM3_PER_CM3,
        ix_i_cm4=contributo_ix_mm4(elemento, y_n_mm) / MM4_PER_CM4,
        iy_i_cm4=contributo_iy_mm4(elemento, x_n_mm) / MM4_PER_CM4,
    )


def run(inputs: SezioneHRimpiattataInput) -> Report[SezioneHRimpiattataOutput]:
    legacy = inputs.legacy_compat
    elementi = costruisci_elementi(inputs.h_profilo_mm, inputs.b_profilo_mm, inputs.tf_mm, inputs.tw_mm,
                                    inputs.piatti, legacy_compat=legacy)
    x_n_mm, y_n_mm = baricentro(elementi, legacy_compat=legacy)
    area_mm2 = area_totale_mm2(elementi)
    ix_mm4, iy_mm4 = inerzia_sezione_mm4(elementi, x_n_mm, y_n_mm)

    riferimento_anima = ALTEZZA_ANIMA_RIFERIMENTO_LEGACY_MM if legacy else None
    profilo = elementi_profilo(inputs.h_profilo_mm, inputs.b_profilo_mm, inputs.tf_mm, inputs.tw_mm,
                                altezza_riferimento_anima_mm=riferimento_anima)
    x_n0_mm, y_n0_mm = baricentro(profilo, legacy_compat=False)
    ix_base_mm4, iy_base_mm4 = inerzia_sezione_mm4(profilo, x_n0_mm, y_n0_mm)

    wel_x_sup, wel_x_inf, wel_y_dx, wel_y_sx = wel_mm3(elementi, ix_mm4, iy_mm4, x_n_mm, y_n_mm)
    if legacy:
        wpl_x, wpl_y = wpl_x_legacy_mm3(elementi, y_n_mm), wpl_y_legacy_mm3(elementi, x_n_mm)
    else:
        wpl_x, wpl_y = wpl_x_mm3(elementi), wpl_y_mm3(elementi)

    sezione = Sezione(
        area_mm2=area_mm2, x_n_mm=x_n_mm, y_n_mm=y_n_mm,
        ix_cm4=ix_mm4 / MM4_PER_CM4, iy_cm4=iy_mm4 / MM4_PER_CM4,
        ix_base_cm4=ix_base_mm4 / MM4_PER_CM4, iy_base_cm4=iy_base_mm4 / MM4_PER_CM4,
        rapporto_ix=ix_mm4 / ix_base_mm4, rapporto_iy=iy_mm4 / iy_base_mm4,
        wel_x_superiore_cm3=wel_x_sup / MM3_PER_CM3, wel_x_inferiore_cm3=wel_x_inf / MM3_PER_CM3,
        wel_y_destro_cm3=wel_y_dx / MM3_PER_CM3, wel_y_sinistro_cm3=wel_y_sx / MM3_PER_CM3,
        wpl_x_cm3=wpl_x / MM3_PER_CM3, wpl_y_cm3=wpl_y / MM3_PER_CM3,
        raggio_x_mm=raggio_giro_mm(ix_mm4, area_mm2), raggio_y_mm=raggio_giro_mm(iy_mm4, area_mm2),
    )
    try:
        schizzo = disegna_schizzo(elementi, x_n_mm, y_n_mm, inputs.h_profilo_mm, inputs.b_profilo_mm)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per acciaio-sezione-h-rimpiattata")
        schizzo = None

    data = SezioneHRimpiattataOutput(
        elementi=tuple(_riga_elemento(e, x_n_mm, y_n_mm) for e in elementi),
        sezione=sezione,
        schizzo=schizzo,
    )
    return success(data, inputs)


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="acciaio-sezione-h-rimpiattata",
        title="Sezione H rimpiattata (profilo + piatti saldati)",
        group="Acciaio / Sezioni",
        norm="EN1993-1-1",
        input_model=SezioneHRimpiattataInput,
        output_model=SezioneHRimpiattataOutput,
        run=run,
        example=ESEMPIO_AUREO,
        summary="Proprietà geometriche di un profilo H saldato con piatti di rinforzo alle ali.",
    ),
)

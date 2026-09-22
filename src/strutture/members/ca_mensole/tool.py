"""Tool registration: ca-mensola-tozza (NTC2018 §4.1.6.1.3, Circ. C4.1.2.1.5 — mensole tozze e
denti Gerber, verifica a bielle e tiranti)."""
import logging

from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .armature import armature
from .capacita import capacita, coefficiente_c
from .geometria import geometria
from .materiali import materiali
from .models import MensolaTozzaInput, MensolaTozzaOutput
from .relazione import relazione
from .schizzo import disegna as disegna_schizzo
from .verifica import verifica_gerarchia, verifica_staffe, verifica_uls

logger = logging.getLogger(__name__)

ESEMPIO_AUREO = {
    "a_mm": 177, "h_mm": 450, "b_mm": 800, "c_mm": 50, "ped_kN": 136, "hed_kN": 0,
    "acciaio": "B450C", "calcestruzzo": "C32/40",
    "n_hor": 8, "phi_hor_mm": 12, "n_incl": 0, "phi_incl_mm": 0, "angolo_incl_deg": 0,
    "n_staffe": 3, "phi_staffe_mm": 12, "staffe_verticali": "NO",
}


def run(inputs: MensolaTozzaInput) -> Report[MensolaTozzaOutput]:
    mat = materiali(inputs.acciaio, inputs.calcestruzzo, legacy_compat=inputs.legacy_compat)
    geo = geometria(inputs.a_mm, inputs.h_mm, inputs.c_mm)
    arm = armature(
        inputs.n_hor, inputs.phi_hor_mm, inputs.n_incl, inputs.phi_incl_mm,
        inputs.a_mm, inputs.h_mm, inputs.ped_kN, mat.fyd_MPa,
    )
    c_coeff = coefficiente_c(inputs.staffe_verticali)
    cap = capacita(
        arm.as_hor_mm2, arm.as_incl_mm2, mat.fyd_MPa, inputs.hed_kN,
        geo.d_mm, geo.l_mm, inputs.b_mm, mat.fcd_MPa, c_coeff, inputs.angolo_incl_deg,
        legacy_compat=inputs.legacy_compat,
    )
    checks = (
        verifica_gerarchia(cap.prs_kN, cap.prc_kN),
        verifica_uls(cap.pr_kN, inputs.ped_kN),
        verifica_staffe(inputs.n_staffe, inputs.phi_staffe_mm, arm.as_lnk_min_mm2),
    )
    try:
        schizzo = disegna_schizzo(inputs, geo)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per ca-mensola-tozza")
        schizzo = None
    data = MensolaTozzaOutput(materiali=mat, geometria=geo, armature=arm, capacita=cap, schizzo=schizzo)
    return success(data, inputs, checks=checks)


TOOLS = (
    Tool(
        name="ca-mensola-tozza",
        title="Progetto e verifica di mensole tozze",
        group="Calcestruzzo armato / Mensole",
        norm="NTC2018 §4.1.6.1.3",
        input_model=MensolaTozzaInput,
        output_model=MensolaTozzaOutput,
        run=run,
        relazione=relazione,
        example=ESEMPIO_AUREO,
        summary="Verifica una mensola tozza in calcestruzzo armato con il modello a bielle e tiranti.",
    ),
)

"""Verified restatement (docs/architecture-phase2.md) of `materiali.py` (`proprieta_materiali`,
NTC2018 Tab. 4.1.V / §4.1.2.1.1.1 / §4.1.2.1.1.3), shared verbatim by both `pilastro-rettangolare`
and `pilastro-circolare` (materials do not depend on the section shape). `f_yk` and `f_ck` feed the
displayed formulas but are not exposed by `MaterialiResult` (only `f_yd`/`f_cd`/`f_tk` are): they
are read straight from the package's own shared lookups (`strutture.shared.materials`), exactly as
the architecture brief allows for a value the output does not itself expose."""
from strutture.shared.materials.concrete.fck import fck
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.relazione import Passo, Traccia, Valore

from .materiali import ALPHA_CC, GAMMA_C, GAMMA_S
from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput


def traccia_materiali(inputs: PilastroInput, output: PilastroOutput) -> Traccia:
    """2 passi: f_yd, f_cd (materiali di calcolo, comuni a rettangolare e circolare)."""
    return Traccia(titolo="Materiali", passi=(_passo_fyd(inputs, output), _passo_fcd(inputs, output)))


def _passo_fyd(inputs: PilastroInput, output: PilastroOutput) -> Passo:
    fyk_MPa = rebar_properties(inputs.acciaio, gamma_s=GAMMA_S).fyk_MPa
    return Passo(
        simbolo="f_yd", formula="f_yk / γ_s",
        valori=(
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa", descrizione=f"tensione caratteristica di snervamento dell'acciaio {inputs.acciaio}"),
            Valore(simbolo="γ_s", valore=GAMMA_S, descrizione="coefficiente parziale di sicurezza dell'acciaio"),
        ),
        risultato=output.materiali.fyd_MPa, unita="MPa", clausola="NTC2018 Tab. 4.1.V / §4.1.2.1.1.3",
        nota="Tensione di calcolo di snervamento dell'acciaio da armatura.",
    )


def _passo_fcd(inputs: PilastroInput, output: PilastroOutput) -> Passo:
    fck_MPa = fck(inputs.cls, legacy_compat=inputs.legacy_compat)
    return Passo(
        simbolo="f_cd", formula="α_cc * f_ck / γ_c",
        valori=(
            Valore(simbolo="α_cc", valore=ALPHA_CC, descrizione="coefficiente riduttivo per le resistenze di lunga durata"),
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione=f"resistenza cilindrica caratteristica del calcestruzzo {inputs.cls}"),
            Valore(simbolo="γ_c", valore=GAMMA_C, descrizione="coefficiente parziale di sicurezza del calcestruzzo"),
        ),
        risultato=output.materiali.fcd_MPa, unita="MPa", clausola="NTC2018 Tab. 4.1.V / §4.1.2.1.1.1",
        nota="Resistenza di calcolo a compressione del calcestruzzo.",
    )

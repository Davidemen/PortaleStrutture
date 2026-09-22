"""Verified restatement (docs/architecture-phase2.md) of `materiali.py` (section/material
properties) and `azione.py` (NTC2018 §7.2.5 / EN1998-5 §5.4.1.2, `NEd = amax·Nsd·α`), shared by
both `norma` branches. `fck`/`fyk` are table lookups (NTC2018 Tab. 4.1.I; rebar grade table,
NTC2018 §11.3.2), cited by identity with a `nota` naming the table (docs/architecture-phase2.md §6:
"a tool whose outputs are a lookup only... formula = the identifier itself"); `fcd`/`fyd` ARE
formulas (NTC2018 §4.1.2.1.1.1 / §11.3.2.1) and are restated fully."""
import math

from strutture.shared.materials.concrete.tables import ALPHA_CC, GAMMA_C
from strutture.shared.materials.rebar.tables import GAMMA_S
from strutture.shared.relazione import Passo, Traccia, Valore

from .azione import AzioneResult
from .materiali import MaterialiResult
from .models import TraviCollegamentoInput
from .sismica_en import SismicaEnResult
from .sismica_ntc import SismicaNtcResult

PI_GRECO = math.pi
CLAUSOLA_FCD = "NTC2018 §4.1.2.1.1.1"
CLAUSOLA_FYD = "NTC2018 §11.3.2.1"
CLAUSOLA_AZIONE = "NTC2018 §7.2.5 / EN1998-5 §5.4.1.2"
Sismica = SismicaNtcResult | SismicaEnResult


def traccia_materiali(inputs: TraviCollegamentoInput, mat: MaterialiResult) -> Traccia:
    """6 passi: Ac, As, fck (lookup), fcd, fyk (lookup), fyd."""
    return Traccia(
        titolo="Materiali e sezione",
        passi=(
            _passo_ac(inputs, mat), _passo_as(inputs, mat), _passo_fck(inputs, mat),
            _passo_fcd(mat), _passo_fyk(inputs, mat), _passo_fyd(mat),
        ),
    )


def traccia_azione(inputs: TraviCollegamentoInput, sismica: Sismica, az: AzioneResult) -> Traccia:
    """2 passi: Nsd, NEd."""
    return Traccia(titolo="Forza assiale di progetto", passi=(_passo_nsd(inputs, az), _passo_ned(sismica, az)))


def _passo_ac(inputs: TraviCollegamentoInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="A_c", formula="B * H",
        valori=(
            Valore(simbolo="B", valore=inputs.b_mm, unita="mm", descrizione="base della sezione"),
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
        ),
        risultato=mat.ac_mm2, unita="mm2",
        nota="Area della sezione di calcestruzzo.",
    )


def _passo_as(inputs: TraviCollegamentoInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="A_s", formula="n * π * φ^2 / 4",
        valori=(
            Valore(simbolo="n", valore=float(inputs.n_barre), descrizione="numero di barre longitudinali"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ", valore=inputs.phi_mm, unita="mm", descrizione="diametro delle barre longitudinali"),
        ),
        risultato=mat.as_mm2, unita="mm2",
        nota="Area delle barre longitudinali.",
    )


def _passo_fck(inputs: TraviCollegamentoInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_ck", formula="f_ck",
        valori=(Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione=f"classe {inputs.classe_calcestruzzo}"),),
        risultato=mat.fck_MPa, unita="MPa",
        nota="Resistenza caratteristica cilindrica, valore tabellare NTC2018 Tab. 4.1.I per la classe scelta.",
    )


def _passo_fcd(mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_cd", formula=f"{ALPHA_CC:g} * f_ck / {GAMMA_C:g}",
        valori=(
            Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione="calcolato sopra"),
        ),
        risultato=mat.fcd_MPa, unita="MPa", clausola=CLAUSOLA_FCD,
        nota=f"Tensione di calcolo a compressione del calcestruzzo (α_cc={ALPHA_CC:g}, γ_c={GAMMA_C:g}).",
    )


def _passo_fyk(inputs: TraviCollegamentoInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_yk", formula="f_yk",
        valori=(Valore(simbolo="f_yk", valore=mat.fyk_MPa, unita="MPa", descrizione=f"classe {inputs.classe_acciaio}"),),
        risultato=mat.fyk_MPa, unita="MPa",
        nota="Tensione caratteristica di snervamento, valore tabellare NTC2018 §11.3.2 per la classe scelta.",
    )


def _passo_fyd(mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_yd", formula=f"f_yk / {GAMMA_S:g}",
        valori=(Valore(simbolo="f_yk", valore=mat.fyk_MPa, unita="MPa", descrizione="calcolato sopra"),),
        risultato=mat.fyd_MPa, unita="MPa", clausola=CLAUSOLA_FYD,
        nota=f"Tensione di calcolo di snervamento dell'acciaio (γ_s={GAMMA_S:g}).",
    )


def _passo_nsd(inputs: TraviCollegamentoInput, az: AzioneResult) -> Passo:
    return Passo(
        simbolo="N_sd", formula="(N_1 + N_2) / 2",
        valori=(
            Valore(simbolo="N_1", valore=inputs.n1_kN, unita="kN", descrizione="forza verticale agente sul primo plinto"),
            Valore(simbolo="N_2", valore=inputs.n2_kN, unita="kN", descrizione="forza verticale agente sul secondo plinto"),
        ),
        risultato=az.nsd_kN, unita="kN", clausola=CLAUSOLA_AZIONE,
        nota="Valore medio delle forze verticali agenti sugli elementi collegati dalla trave.",
    )


def _passo_ned(sismica: Sismica, az: AzioneResult) -> Passo:
    return Passo(
        simbolo="N_Ed", formula="a_max * N_sd * α",
        valori=(
            Valore(simbolo="a_max", valore=sismica.amax_g, unita="g", descrizione="accelerazione orizzontale massima attesa al sito, calcolata sopra"),
            Valore(simbolo="N_sd", valore=az.nsd_kN, unita="kN", descrizione="calcolato sopra"),
            Valore(simbolo="α", valore=sismica.alpha, descrizione="coefficiente tabellare, calcolato sopra"),
        ),
        risultato=az.ned_kN, unita="kN", clausola=CLAUSOLA_AZIONE,
        nota="Forza assiale di progetto della trave di collegamento.",
    )

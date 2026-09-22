"""Verified restatement of `ca-apertura-fessure`'s geometry (`geometria_fessurazione.py`, Circ.
2019 §C4.1.2.2.4.5 / EN 1992-1-1 §7.3.4) and materials/coefficients (`strutture.shared.materials.
concrete`, NTC2018 §4.1.2.1.1; `coefficienti_fessurazione.py`, Circ. 2019 §C4.1.6-§C4.1.9) steps
of `docs/architecture-phase2.md` §6 wave 2/3. `f_ck` is a Tab. 4.1.I lookup (bare-identifier
`Passo`, §6's "no formula" rule); `k_1`/`k_2`/`k_t` are Tab. C4.1.6-9 lookups the same way. Called
by `relazione_apertura_fessure.py`, which owns the tool-level assembly and the remaining traces."""
import math

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.concrete.resistenze import CEMENT_AGING_EXPONENT, FCM_OVER_FCK_MPA, FCTM_COEFFICIENT
from strutture.shared.relazione import Passo, Traccia, Valore

from .geometria_fessurazione import altezza_efficace_mm, area_efficace_mm2, diametro_equivalente_mm
from .models import AperturaFessureInput, AperturaFessureOutput, MaterialeFessurazioneOutput

CLAUSOLA_GEOMETRIA = "Circ. 2019 §C4.1.2.2.4.5"
CLAUSOLA_PHI_EQ = "Circ. 2019 §C4.1.8 / EN 1992-1-1 §7.3.4"
CLAUSOLA_RHO_EFF = "Circ. 2019 §C4.1.2.2.4.5 / EN 1992-1-1 §7.3.4"
CLAUSOLA_MATERIALI = "NTC2018 §4.1.2.1.1"


def traccia_geometria(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Traccia:
    """6 passi: d, h_c,eff, A_c,eff, A_s, φ_eq, ρ_eff."""
    geometria = output.geometria
    return Traccia(
        titolo="Geometria della sezione fessurata",
        passi=(
            _passo_d(inputs, geometria.d_mm),
            _passo_hc_eff(inputs, geometria.d_mm, geometria.hc_eff_mm),
            _passo_ac_eff(inputs, geometria.hc_eff_mm, geometria.ac_eff_mm2),
            _passo_as(inputs, geometria.as_mm2),
            _passo_phi_eq(inputs, geometria.phi_eq_mm),
            _passo_rho_eff(geometria.as_mm2, geometria.ac_eff_mm2, geometria.rho_eff),
        ),
    )


def _passo_d(inputs: AperturaFessureInput, d_mm: float) -> Passo:
    return Passo(
        simbolo="d", formula="h - φ_1/2 - c",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="φ_1", valore=inputs.phi1_mm, unita="mm", descrizione="diametro delle barre, gruppo 1"),
            Valore(simbolo="c", valore=inputs.copriferro_mm, unita="mm", descrizione="copriferro dell'armatura"),
        ),
        risultato=d_mm, unita="mm", clausola=CLAUSOLA_GEOMETRIA, nota="Altezza utile della sezione.",
    )


def _passo_hc_eff(inputs: AperturaFessureInput, d_mm: float, hc_eff_mm: float) -> Passo:
    return Passo(
        simbolo="h_c,eff", formula="min(2.5 * (h - d), (h - x) / 3, h / 2)",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="d", valore=d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="x", valore=inputs.x_mm, unita="mm", descrizione="profondità dell'asse neutro"),
        ),
        risultato=altezza_efficace_mm(inputs.h_mm, d_mm, inputs.x_mm), unita="mm",
        clausola=CLAUSOLA_GEOMETRIA, nota="Altezza efficace di calcestruzzo teso attorno all'armatura.",
    )


def _passo_ac_eff(inputs: AperturaFessureInput, hc_eff_mm: float, ac_eff_mm2: float) -> Passo:
    return Passo(
        simbolo="A_c,eff", formula="h_c,eff * b",
        valori=(
            Valore(simbolo="h_c,eff", valore=hc_eff_mm, unita="mm", descrizione="altezza efficace, calcolata sopra"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="larghezza della sezione"),
        ),
        risultato=area_efficace_mm2(hc_eff_mm, inputs.b_mm), unita="mm2",
        clausola=CLAUSOLA_GEOMETRIA, nota="Area efficace di calcestruzzo teso attorno all'armatura.",
    )


def _passo_as(inputs: AperturaFessureInput, as_mm2: float) -> Passo:
    return Passo(
        simbolo="A_s", formula="n_1 * π/4 * φ_1^2 + n_2 * π/4 * φ_2^2",
        valori=(
            Valore(simbolo="n_1", valore=inputs.n1, descrizione="numero di barre, gruppo 1"),
            Valore(simbolo="φ_1", valore=inputs.phi1_mm, unita="mm"),
            Valore(simbolo="n_2", valore=inputs.n2, descrizione="numero di barre, gruppo 2 (0 se assente)"),
            Valore(simbolo="φ_2", valore=inputs.phi2_mm, unita="mm", descrizione="diametro delle barre, gruppo 2 (0 se assente)"),
            Valore(simbolo="π", valore=math.pi, descrizione="pi greco"),
        ),
        risultato=as_mm2, unita="mm2", nota="Area di armatura tesa presente.",
    )


def _passo_phi_eq(inputs: AperturaFessureInput, phi_eq_mm: float) -> Passo:
    return Passo(
        simbolo="φ_eq", formula="(n_1 * φ_1^2 + n_2 * φ_2^2) / (n_1 * φ_1 + n_2 * φ_2)",
        valori=(
            Valore(simbolo="n_1", valore=inputs.n1),
            Valore(simbolo="φ_1", valore=inputs.phi1_mm, unita="mm"),
            Valore(simbolo="n_2", valore=inputs.n2),
            Valore(simbolo="φ_2", valore=inputs.phi2_mm, unita="mm"),
        ),
        risultato=diametro_equivalente_mm(inputs.n1, inputs.phi1_mm, inputs.n2, inputs.phi2_mm), unita="mm",
        clausola=CLAUSOLA_PHI_EQ, nota="Diametro equivalente delle barre tese (media pesata sull'area).",
    )


def _passo_rho_eff(as_mm2: float, ac_eff_mm2: float, rho_eff: float) -> Passo:
    return Passo(
        simbolo="ρ_eff", formula="A_s / A_c,eff",
        valori=(
            Valore(simbolo="A_s", valore=as_mm2, unita="mm2", descrizione="armatura tesa, calcolata sopra"),
            Valore(simbolo="A_c,eff", valore=ac_eff_mm2, unita="mm2", descrizione="area efficace di calcestruzzo teso, calcolata sopra"),
        ),
        risultato=rho_eff, unita="-", clausola=CLAUSOLA_RHO_EFF, nota="Rapporto di armatura efficace.",
    )


def traccia_materiali(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Traccia:
    """8 passi: f_ck (lookup), f_cm, E_cm, f_ctm, α_e, k_1, k_2, k_t (i primi tre lookup)."""
    materiale, coefficienti = output.materiale, output.coefficienti
    fck_MPa = _fck_da_classe(inputs.classe_calcestruzzo)
    fcm_MPa = fck_MPa + FCM_OVER_FCK_MPA
    return Traccia(
        titolo="Materiali e coefficienti di calcolo",
        passi=(
            _passo_fck(inputs, fck_MPa),
            _passo_fcm(fck_MPa, fcm_MPa),
            _passo_ecm(fcm_MPa, materiale.ecm_MPa),
            _passo_fctm(fck_MPa, materiale.fctm_MPa),
            _passo_alpha_e(inputs, materiale),
            _passo_lookup("k_1", coefficienti.k1, inputs.tipo_barre, "Circ. 2019 §C4.1.7", "coefficiente di aderenza delle barre"),
            _passo_lookup("k_2", coefficienti.k2, inputs.tipo_sollecitazione, "Circ. 2019 §C4.1.9", "coefficiente per tipo di sollecitazione"),
            _passo_lookup("k_t", coefficienti.kt, inputs.durata_carico, "Circ. 2019 §C4.1.6", "coefficiente per durata del carico"),
        ),
    )


def _fck_da_classe(classe_calcestruzzo: str) -> float:
    return concrete_properties(classe_calcestruzzo).fck_MPa


def _passo_fck(inputs: AperturaFessureInput, fck_MPa: float) -> Passo:
    return Passo(
        simbolo="f_ck", formula="f_ck",
        valori=(Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione=f"resistenza cilindrica caratteristica per la classe {inputs.classe_calcestruzzo}"),),
        risultato=fck_MPa, unita="MPa", nota="Lettura di NTC2018 Tab. 4.1.I per la classe di calcestruzzo scelta.",
    )


def _passo_fcm(fck_MPa: float, fcm_MPa: float) -> Passo:
    return Passo(
        simbolo="f_cm", formula=f"f_ck + {FCM_OVER_FCK_MPA:g}",
        valori=(Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),),
        risultato=fcm_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI, nota="Resistenza cilindrica media a compressione.",
    )


def _passo_ecm(fcm_MPa: float, ecm_MPa: float) -> Passo:
    return Passo(
        simbolo="E_cm", formula=f"22000 * (f_cm / 10)^{CEMENT_AGING_EXPONENT:g}",
        valori=(Valore(simbolo="f_cm", valore=fcm_MPa, unita="MPa", descrizione="resistenza cilindrica media, calcolata sopra"),),
        risultato=ecm_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI, nota="Modulo elastico secante del calcestruzzo.",
    )


def _passo_fctm(fck_MPa: float, fctm_MPa: float) -> Passo:
    return Passo(
        simbolo="f_ctm", formula=f"{FCTM_COEFFICIENT:g} * f_ck^(2/3)",
        valori=(Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),),
        risultato=fctm_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI,
        nota="Resistenza media a trazione del calcestruzzo (classi ≤ C50/60).",
    )


def _passo_alpha_e(inputs: AperturaFessureInput, materiale: MaterialeFessurazioneOutput) -> Passo:
    return Passo(
        simbolo="α_e", formula="E_s / E_cm",
        valori=(
            Valore(simbolo="E_s", valore=inputs.es_MPa, unita="MPa", descrizione="modulo elastico dell'acciaio"),
            Valore(simbolo="E_cm", valore=materiale.ecm_MPa, unita="MPa", descrizione="modulo elastico secante del calcestruzzo, calcolato sopra"),
        ),
        risultato=materiale.alpha_e, unita="-", clausola="EN 1992-1-1 §7.3.4",
        nota="Rapporto di omogeneizzazione acciaio-calcestruzzo, usato nella deformazione media dell'armatura.",
    )


def _passo_lookup(simbolo: str, valore: float, chiave: str, clausola: str, descrizione: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione=f"{descrizione}: '{chiave}'"),),
        risultato=valore, unita="-", clausola=clausola, nota=f"Lettura tabellare, {clausola}.",
    )

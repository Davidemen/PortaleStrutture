"""Verified restatement (docs/architecture-phase2.md §6) of the reference kinetic pressure q_r
(`pressione_cinetica.py`, NTC2018 §3.3.6 — renamed from the code's own `q_b`: EN1991-1-4 §4.5 calls
q_b the pressure built on v_b, while this quantity is built on v_r, the return-period velocity;
keeping the code's `q_b` label on the printed trace would be a symbol clash a reader could mistake
for the Eurocode quantity, review finding WRONG_CLAUSE), the exposure coefficient at the building
height c_e(H) (`esposizione.py::coefficiente_esposizione`, NTC2018 §3.3.7) and the design pressure
p(H) = q_r·c_e(H)·c_p·c_d (NTC2018 §3.3.4 "Azione del vento"). `output.p_h_kNm2` is computed by the
tool with an implicit c_p=c_d=1 (`tool.py::run`): the passo below makes both factors EXPLICIT
Valore of 1 rather than silently dropping them, so the printed formula is the norm's own formula,
not a peak-pressure value passed off as the full design pressure under the same clause (review
finding WRONG_CLAUSE — the previous `q_b·c_eH` formula was, in fact, only the peak/kinetic pressure
q_r·c_e(H) of §3.3.6/§3.3.7, not §3.3.4's p). The calculation code is never touched — the result is
unchanged since multiplying by two explicit 1's changes nothing: `esposizione.coefficiente_esposizione`
computes `z_eff=max(z, z_min)` and reuses the resulting log term twice in its own formula; the c_e(H)
passo below restates that same sub-expression twice rather than inventing an intermediate the code
never names (the same "reuse a formula fragment" technique
`ca_travi/relazione_taglio.py::_sin2_theta_formula` uses for cotg θ)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .costanti import AIR_DENSITY_KG_M3, PA_TO_KN_M2
from .models import VentoPressioneInput, VentoPressioneOutput

CLAUSOLA_QR = "NTC2018 §3.3.6"
CLAUSOLA_CE = "NTC2018 §3.3.7"
CLAUSOLA_P = "NTC2018 §3.3.4"


def traccia_pressione(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Traccia:
    """3 passi: q_r, c_e(H), p(H)."""
    return Traccia(titolo="Pressione cinetica e coefficiente di esposizione", passi=(_passo_qr(output), _passo_ceh(inputs, output), _passo_ph(output)))


def _passo_qr(output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="q_r",
        formula="0.5 * ρ * v_r^2",
        valori=(
            Valore(simbolo="ρ", valore=AIR_DENSITY_KG_M3, unita="kg/m³", descrizione="densità dell'aria"),
            Valore(simbolo="v_r", valore=output.vr, unita="m/s", descrizione="velocità di riferimento, calcolata sopra"),
        ),
        risultato=output.qb, unita="kN/m²", scala=1.0 / PA_TO_KN_M2, clausola=CLAUSOLA_QR,
        nota="Pressione cinetica di riferimento per il periodo di ritorno di progetto (Pa convertiti in kN/m² tramite il fattore di scala).",
    )


def _passo_ceh(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="c_e(H)",
        formula="k_r^2 * (c_t * ln(max(H, z_min) / z_0)) * (7 + c_t * ln(max(H, z_min) / z_0))",
        valori=(
            Valore(simbolo="k_r", valore=output.kr, descrizione="fattore di terreno, calcolato sopra"),
            Valore(simbolo="c_t", valore=inputs.ct, descrizione="coefficiente di topografia, dato di ingresso"),
            Valore(simbolo="H", valore=inputs.altezza_edificio_m, unita="m", descrizione="altezza massima dell'edificio"),
            Valore(simbolo="z_min", valore=output.zmin, unita="m", descrizione="quota minima del profilo, calcolata sopra"),
            Valore(simbolo="z_0", valore=output.z0, unita="m", descrizione="lunghezza di rugosità del terreno, calcolata sopra"),
        ),
        risultato=output.ce_h, unita="-", clausola=CLAUSOLA_CE,
        nota="Coefficiente di esposizione alla quota dell'edificio; sotto z_min il coefficiente resta costante.",
    )


def _passo_ph(output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="p(H)",
        formula="q_r * c_eH * c_p * c_d",
        valori=(
            Valore(simbolo="q_r", valore=output.qb, unita="kN/m²", descrizione="pressione cinetica di riferimento, calcolata sopra"),
            Valore(simbolo="c_eH", valore=output.ce_h, descrizione="coefficiente di esposizione alla quota dell'edificio, calcolato sopra"),
            Valore(simbolo="c_p", valore=1.0, descrizione="coefficiente di forma, assunto unitario: questo strumento non calcola c_p (vedi vento-cpe)"),
            Valore(simbolo="c_d", valore=1.0, descrizione="coefficiente dinamico, assunto unitario: questo strumento non lo calcola"),
        ),
        risultato=output.p_h_kNm2, unita="kN/m²", clausola=CLAUSOLA_P,
        nota="Pressione del vento alla quota dell'edificio, con c_p=c_d=1: per la pressione su una "
        "superficie reale applicare il c_p di vento-cpe e il c_d di progetto.",
    )

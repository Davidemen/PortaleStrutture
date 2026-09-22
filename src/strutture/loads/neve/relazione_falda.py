"""Verified restatement (docs/architecture-phase2.md §6) of the roof shape coefficient μ
(`forma_falda.py::coefficiente_forma`, NTC2018 §3.4.5.2 Tab. 3.4.II / EN 1991-1-3 Tab. 5.2 — the
same table under two names) and the design snow load q_s = q_sk·C_E·C_t·μ (NTC2018 §3.4.1 eq.
3.4.1, `tool.py::run_carico_falda`). The calculation code is never touched.

Fixed-mode `coefficiente_forma` is a 3-branch piecewise function of the pitch angle (flat/ramp/
steep) when there is no parapet; the SAME closed-form clamp `min(μ_max, max(μ_min, μ_max·(α_max−α)
/(α_max−α_min)))` reproduces all three branches (verified against `forma_falda.py` for α∈[0°,90°]),
so a single formula covers them and only the parapet/no-parapet branch needs its own formula text —
the parapet branch is a pure lookup (`docs/architecture-phase2.md`'s "formula = the identifier
itself" pattern for a value with no formula an engineer would write). The four table breakpoints
(μ_max, μ_min, α_min, α_max) get their OWN passo each — reused, unchanged, by both pitches on a
"due falde" roof, the same reuse-a-derived-value pattern `ca_travi/relazione_geometria.py::_passo_z`
uses — rather than only living inside the μ formula's `valori`.

`numero` ("", "1", "2") builds identifiers matching `CaricoFaldaOutput`'s own UI symbol hints
EXACTLY: μ/μ_1/μ_2 (underscore) but q_s/q_s1/q_s2 (NO underscore) and α/α_1/α_2 (underscore, matching
`CaricoFaldaInput.a`/`a1`/`a2`) — the two output families use different subscript spelling, so a
single "etichetta" suffix cannot build both correctly."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .forma_falda import ANGLE_HIGH_DEG, ANGLE_LOW_DEG, MU_FLAT, MU_STEEP
from .models import CaricoFaldaInput, CaricoFaldaOutput

CLAUSOLA_MU = "NTC2018 §3.4.5.2 Tab. 3.4.II / EN 1991-1-3 Tab. 5.2"
CLAUSOLA_QS = "NTC2018 §3.4.1 eq. (3.4.1)"


def traccia_falde(inputs: CaricoFaldaInput, output: CaricoFaldaOutput) -> Traccia:
    """6 passi (copertura ad una falda: le 4 soglie + μ + q_s) o 8 (due falde: le 4 soglie,
    condivise, + μ_1, q_s1, μ_2, q_s2)."""
    if output.qs is not None:
        titolo = "Carico neve di progetto — copertura ad una falda"
        passi = (
            *_passi_soglie(),
            *_passi_falda(numero="", alpha_deg=inputs.a, parapetto=inputs.parapetto == "SI",
                          mu_val=output.mu, qs_val=output.qs, output=output, ct_val=inputs.ct),
        )
    else:
        titolo = "Carico neve di progetto — copertura a due falde"
        passi = (
            *_passi_soglie(),
            *_passi_falda(numero="1", alpha_deg=inputs.a1, parapetto=inputs.parapetto1 == "SI",
                           mu_val=output.mu1, qs_val=output.qs1, output=output, ct_val=inputs.ct),
            *_passi_falda(numero="2", alpha_deg=inputs.a2, parapetto=inputs.parapetto2 == "SI",
                           mu_val=output.mu2, qs_val=output.qs2, output=output, ct_val=inputs.ct),
        )
    return Traccia(titolo=titolo, passi=passi)


def _passi_soglie() -> tuple[Passo, Passo, Passo, Passo]:
    """μ_max/μ_min/α_min/α_max: le 4 soglie di Tab. 3.4.II, ciascuna una pura lettura da tabella."""
    return (
        Passo(
            simbolo="μ_max", formula="μ_max",
            valori=(Valore(simbolo="μ_max", valore=MU_FLAT),),
            risultato=MU_FLAT, unita="-", clausola=CLAUSOLA_MU,
            nota="Coefficiente di forma massimo, per α ≤ α_min.",
        ),
        Passo(
            simbolo="μ_min", formula="μ_min",
            valori=(Valore(simbolo="μ_min", valore=MU_STEEP),),
            risultato=MU_STEEP, unita="-", clausola=CLAUSOLA_MU,
            nota="Coefficiente di forma minimo, per α ≥ α_max.",
        ),
        Passo(
            simbolo="α_min", formula="α_min",
            valori=(Valore(simbolo="α_min", valore=ANGLE_LOW_DEG, unita="°"),),
            risultato=ANGLE_LOW_DEG, unita="°", clausola=CLAUSOLA_MU,
            nota="Angolo di falda fino al quale μ resta al valore massimo.",
        ),
        Passo(
            simbolo="α_max", formula="α_max",
            valori=(Valore(simbolo="α_max", valore=ANGLE_HIGH_DEG, unita="°"),),
            risultato=ANGLE_HIGH_DEG, unita="°", clausola=CLAUSOLA_MU,
            nota="Angolo di falda oltre il quale μ si annulla.",
        ),
    )


def _passi_falda(
    *, numero: str, alpha_deg: float, parapetto: bool, mu_val: float, qs_val: float,
    output: CaricoFaldaOutput, ct_val: float,
) -> tuple[Passo, Passo]:
    simbolo_mu = f"μ_{numero}" if numero else "μ"
    passo_mu = _passo_mu(simbolo_mu, numero, alpha_deg, parapetto, mu_val)
    passo_qs = _passo_qs(f"q_s{numero}", simbolo_mu, mu_val, ct_val, output, qs_val)
    return passo_mu, passo_qs


def _passo_mu(simbolo: str, numero: str, alpha_deg: float, parapetto: bool, mu_val: float) -> Passo:
    etichetta_falda = f" {numero}" if numero else ""
    if parapetto:
        return Passo(
            simbolo=simbolo,
            formula="μ_max",
            valori=(Valore(simbolo="μ_max", valore=MU_FLAT, descrizione="valore massimo del coefficiente di forma, calcolato sopra"),),
            risultato=mu_val, unita="-", clausola=CLAUSOLA_MU,
            nota=f"Presenza di barriera al bordo inferiore della falda{etichetta_falda}: il coefficiente "
                 f"resta al valore massimo, indipendentemente dall'angolo α={alpha_deg:g}°.",
        )
    alpha_simbolo = f"α_{numero}" if numero else "α"
    return Passo(
        simbolo=simbolo,
        formula=f"min(μ_max, max(μ_min, μ_max * (α_max - {alpha_simbolo}) / (α_max - α_min)))",
        valori=(
            Valore(simbolo="μ_max", valore=MU_FLAT, descrizione="coefficiente massimo, calcolato sopra"),
            Valore(simbolo="μ_min", valore=MU_STEEP, descrizione="coefficiente minimo, calcolato sopra"),
            Valore(simbolo=alpha_simbolo, valore=alpha_deg, unita="°", descrizione="angolo della falda"),
            Valore(simbolo="α_min", valore=ANGLE_LOW_DEG, unita="°", descrizione="soglia inferiore, calcolata sopra"),
            Valore(simbolo="α_max", valore=ANGLE_HIGH_DEG, unita="°", descrizione="soglia superiore, calcolata sopra"),
        ),
        risultato=mu_val, unita="-", clausola=CLAUSOLA_MU,
        nota="Rampa lineare tra il valore massimo (α≤α_min) e il valore minimo (α≥α_max).",
    )


def _passo_qs(simbolo: str, simbolo_mu: str, mu_val: float, ct_val: float, output: CaricoFaldaOutput, qs_val: float) -> Passo:
    return Passo(
        simbolo=simbolo,
        formula=f"q_sk * C_E * C_t * {simbolo_mu}",
        valori=(
            Valore(simbolo="q_sk", valore=output.qsk, unita="kN/m²", descrizione="carico neve al suolo, calcolato sopra"),
            Valore(simbolo="C_E", valore=output.ce, descrizione="coefficiente di esposizione, calcolato sopra"),
            Valore(simbolo="C_t", valore=ct_val, descrizione="coefficiente termico, calcolato sopra"),
            Valore(simbolo=simbolo_mu, valore=mu_val, descrizione="coefficiente di forma, calcolato sopra"),
        ),
        risultato=qs_val, unita="kN/m²", clausola=CLAUSOLA_QS,
        nota="Carico neve di progetto sulla copertura.",
    )

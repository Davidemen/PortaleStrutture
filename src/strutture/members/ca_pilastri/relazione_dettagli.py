"""Verified restatement (docs/architecture-phase2.md) of `confinamento.py` (NTC2018 §7.4.6.2.2,
confined critical-zone stirrup spacing) and `dettagli.py` (NTC2018 §4.1.6.1.2 / §7.4.6.2.2,
longitudinal-bar spacing and minimum stirrup diameter/spacing). Every value here is consumed by
exactly one `Check`, so — mirroring `ca_travi.relazione_armatura` — derivation and comparison are
combined into a single `Passo`, the same pattern `docs/architecture-phase2.md`'s own worked example
uses. `legacy_compat=False` throughout: only the code-standard branch of each `RuleSet` (`regole.py`)
is restated (`relazione` never runs in Excel mode)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .confinamento import (
    CONFINED_SPACING_FIXED_MM,
    CONFINED_SPACING_HALF_DIMENSION,
    CONFINED_SPACING_LONG_BAR_MULTIPLIER,
)
from .dettagli import STIRRUP_MIN_DIAMETER_BAR_DIVISOR, STIRRUP_MIN_DIAMETER_FIXED_MM
from .models import DettagliResult, Norma, PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .regole import RuleSet, resolve

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput

_CLAUSOLA_DIAMETRO_LONG_MIN: dict[Norma, str] = {"NTC2018": "NTC2018 §4.1.6.1.2", "EC2": "EN 1992-1-1 §9.5.2(1)"}
# Review finding (WRONG_CLAUSE): s_staffe,max/φ_sw,min sono dettaglio ORDINARIO (interasse/diametro
# minimo delle staffe fuori dalla zona critica), non il dettaglio SISMICO di zona critica confinata
# (NTC2018 §7.4.6.2.2, già citato correttamente da `traccia_confinamento` per la stessa clausola).
_CLAUSOLA_INTERASSE_STAFFE: dict[Norma, str] = {"NTC2018": "NTC2018 §4.1.6.1.2", "EC2": "EN 1992-1-1 §9.5.3(1)"}
_CLAUSOLA_DIAMETRO_STAFFE_MIN: dict[Norma, str] = {"NTC2018": "NTC2018 §4.1.6.1.2", "EC2": "EN 1992-1-1 §9.5.3(1)"}


def traccia_confinamento(inputs: PilastroInput, output: PilastroOutput, *, dimensione_confinata_mm: float) -> Traccia:
    """1 passo: passo massimo delle staffe nella zona critica confinata (Check "Passo delle staffe
    in zona critica"), NTC2018 §7.4.6.2.2. `dimensione_confinata_mm` è il lato minore della sezione
    (rettangolare) o il lato del quadrato equivalente (circolare, come nelle formule di taglio)."""
    confinamento = output.confinamento
    soddisfatta = inputs.passo_staffe_mm <= confinamento.passo_max_confinato_mm
    passo = Passo(
        simbolo="s_max,cr",
        formula=f"min(dimensione_cr / {CONFINED_SPACING_HALF_DIMENSION:g}, {CONFINED_SPACING_FIXED_MM:g}, "
                f"{CONFINED_SPACING_LONG_BAR_MULTIPLIER:g} * φ) >= s",
        valori=(
            Valore(simbolo="dimensione_cr", valore=dimensione_confinata_mm, unita="mm",
                   descrizione="dimensione della sezione confinata (lato minore rettangolare, lato equivalente circolare)"),
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm", descrizione="diametro dei ferri longitudinali"),
            Valore(simbolo="s", valore=inputs.passo_staffe_mm, unita="mm", descrizione="passo delle staffe presente"),
        ),
        risultato=confinamento.passo_max_confinato_mm, unita="mm", clausola="NTC2018 §7.4.6.2.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Passo massimo delle staffe nella zona critica confinata (altezza h_cr alle estremità del pilastro).",
    )
    return Traccia(titolo="Confinamento della zona critica", passi=(passo,))


def traccia_dettagli_rettangolare(inputs: PilastroRettangolareInput, output: PilastroOutput) -> Traccia:
    rules = resolve(inputs.norma, legacy_compat=False)
    interasse_formula = "(2 * ((L_1 - 2 * c) + (L_2 - 2 * c))) / n_ferri <= s_ferri,max"
    interasse_valori = (
        Valore(simbolo="L_1", valore=inputs.l1_mm, unita="mm"),
        Valore(simbolo="L_2", valore=inputs.l2_mm, unita="mm"),
        Valore(simbolo="c", valore=inputs.c_mm, unita="mm", descrizione="copriferro"),
        Valore(simbolo="n_ferri", valore=float(inputs.n_ferri)),
    )
    dimensione_min_mm = min(inputs.l1_mm, inputs.l2_mm) if rules.staffe_min_dimensione else None
    passi = _passi_comuni(inputs, output, rules, interasse_formula, interasse_valori, dimensione_min_mm, "min(L_1, L_2)")
    return Traccia(titolo="Dettagli costruttivi", passi=passi)


def traccia_dettagli_circolare(inputs: PilastroCircolareInput, output: PilastroOutput) -> Traccia:
    rules = resolve(inputs.norma, legacy_compat=False)
    interasse_formula = "(2 * π * (D / 2 - c)) / n_ferri <= s_ferri,max"
    interasse_valori = (
        Valore(simbolo="π", valore=3.141592653589793),
        Valore(simbolo="D", valore=inputs.d_mm, unita="mm"),
        Valore(simbolo="c", valore=inputs.c_mm, unita="mm", descrizione="copriferro"),
        Valore(simbolo="n_ferri", valore=float(inputs.n_ferri)),
    )
    dimensione_min_mm = inputs.d_mm if rules.staffe_min_dimensione else None
    passi = _passi_comuni(inputs, output, rules, interasse_formula, interasse_valori, dimensione_min_mm, "D")
    return Traccia(titolo="Dettagli costruttivi", passi=passi)


def _passi_comuni(
    inputs: PilastroInput, output: PilastroOutput, rules: RuleSet,
    interasse_formula: str, interasse_valori: tuple[Valore, ...],
    dimensione_min_mm: float | None, dimensione_min_descrizione: str,
) -> tuple[Passo, ...]:
    dettagli = output.dettagli
    passi = (
        _passo_interasse_long(inputs, dettagli, interasse_formula, interasse_valori),
        _passo_diametro_long_min(inputs, dettagli, rules),
        _passo_diametro_staffe_min(inputs, dettagli),
        _passo_interasse_staffe_max(inputs, dettagli, rules, dimensione_min_mm, dimensione_min_descrizione),
    )
    if rules.as_max_check:
        passi = (*passi, _passo_as_max(output))
    return passi


def _passo_interasse_long(inputs: PilastroInput, dettagli: DettagliResult, formula: str, valori: tuple[Valore, ...]) -> Passo:
    soddisfatta = dettagli.interasse_long_calcolato_mm <= dettagli.interasse_long_max_mm
    return Passo(
        simbolo="s_ferri", formula=formula,
        valori=(*valori, Valore(simbolo="s_ferri,max", valore=dettagli.interasse_long_max_mm, unita="mm",
                                 descrizione="interasse massimo tra le barre longitudinali, NTC2018 §7.4.6.2.2 (zona sismica)")),
        risultato=dettagli.interasse_long_calcolato_mm, unita="mm", clausola="NTC2018 §7.4.6.2.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Interasse tra le barre longitudinali, dedotto dal perimetro della gabbia di armatura.",
    )


def _passo_diametro_long_min(inputs: PilastroInput, dettagli: DettagliResult, rules: RuleSet) -> Passo:
    """Il diametro minimo normativo (`rules.diametro_long_min_mm`, 12 mm NTC2018 / 8 mm EC2) è una
    costante fissa senza ulteriore formula: è quindi scritta come letterale (come `AS_MIN_RHO_
    ASSOLUTO` in `ca_travi.relazione_armatura`), non come un `Valore` identico al `simbolo` del
    passo stesso."""
    soddisfatta = dettagli.diametro_long_min_mm <= inputs.diametro_ferri_mm
    return Passo(
        simbolo="φ_long,min", formula=f"{dettagli.diametro_long_min_mm:g} <= φ",
        valori=(
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm", descrizione="diametro dei ferri longitudinali"),
        ),
        risultato=dettagli.diametro_long_min_mm, unita="mm", clausola=_CLAUSOLA_DIAMETRO_LONG_MIN[inputs.norma],
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Diametro minimo delle barre longitudinali (12 mm per NTC2018, 8 mm per EC2 — Allegato Nazionale escluso).",
    )


def _passo_diametro_staffe_min(inputs: PilastroInput, dettagli: DettagliResult) -> Passo:
    soddisfatta = dettagli.diametro_staffe_min_mm <= inputs.diametro_staffe_mm
    return Passo(
        simbolo="φ_sw,min", formula=f"max({STIRRUP_MIN_DIAMETER_FIXED_MM:g}, φ / {STIRRUP_MIN_DIAMETER_BAR_DIVISOR:g}) <= φ_sw",
        valori=(
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm", descrizione="diametro dei ferri longitudinali"),
            Valore(simbolo="φ_sw", valore=inputs.diametro_staffe_mm, unita="mm", descrizione="diametro delle staffe presente"),
        ),
        risultato=dettagli.diametro_staffe_min_mm, unita="mm", clausola=_CLAUSOLA_DIAMETRO_STAFFE_MIN[inputs.norma],
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Diametro minimo delle staffe: il maggiore fra 6 mm e un quarto del diametro dei ferri longitudinali.",
    )


def _passo_interasse_staffe_max(
    inputs: PilastroInput, dettagli: DettagliResult, rules: RuleSet, dimensione_min_mm: float | None, dimensione_min_descrizione: str,
) -> Passo:
    soddisfatta = inputs.passo_staffe_mm <= dettagli.interasse_staffe_max_mm
    if dimensione_min_mm is not None:
        formula = f"min({rules.staffe_bar_multiplier:g} * φ, {rules.staffe_fixed_mm:g}, dimensione_min) >= s"
        valori = (
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm"),
            Valore(simbolo="dimensione_min", valore=dimensione_min_mm, unita="mm", descrizione=dimensione_min_descrizione),
            Valore(simbolo="s", valore=inputs.passo_staffe_mm, unita="mm", descrizione="passo delle staffe presente"),
        )
    else:
        formula = f"min({rules.staffe_bar_multiplier:g} * φ, {rules.staffe_fixed_mm:g}) >= s"
        valori = (
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm"),
            Valore(simbolo="s", valore=inputs.passo_staffe_mm, unita="mm", descrizione="passo delle staffe presente"),
        )
    return Passo(
        simbolo="s_staffe,max", formula=formula, valori=valori,
        risultato=dettagli.interasse_staffe_max_mm, unita="mm", clausola=_CLAUSOLA_INTERASSE_STAFFE[inputs.norma],
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Interasse massimo delle staffe fuori dalla zona critica.",
    )


def _passo_as_max(output: PilastroOutput) -> Passo:
    """EC2-only (`Check` "Area massima di armatura longitudinale", EC2 §9.5.2(3)): A_s è già stato
    derivato nella Traccia "Geometria della sezione"."""
    geometria = output.geometria
    as_max_mm2 = 0.04 * geometria.ac_mm2
    soddisfatta = geometria.as_mm2 <= as_max_mm2
    return Passo(
        simbolo="A_s,max", formula="A_s <= 0.04 * A_c",
        valori=(
            Valore(simbolo="A_s", valore=geometria.as_mm2, unita="mm2"),
            Valore(simbolo="A_c", valore=geometria.ac_mm2, unita="mm2"),
        ),
        risultato=geometria.as_mm2, unita="mm2", clausola="EN 1992-1-1 §9.5.2(3)",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Area massima di armatura longitudinale ammessa (4% dell'area di calcestruzzo), verifica propria di EC2.",
    )

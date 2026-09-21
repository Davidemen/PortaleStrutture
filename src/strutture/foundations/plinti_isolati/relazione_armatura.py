"""`relazione.py` (docs/architecture-phase2.md §6): cantilever bending moment at the column/
pedestal face and the required flexural reinforcement, both directions (`momento_cantilever.py`/
`flessione.py`, docs/specs/fond-plinti-isolati.md Tool-2 steps 8-9). `σ_SLU` — the MAX contact
pressure over the ULS-type famiglie (`flessione.mead_families`), not necessarily the sigma-
governing row of `relazione_azioni.py` — is picked by calling the package's own `max_pressione_kpa`
step function, exactly as `flessione()` does; `_riga_slu_governante` additionally names, for the
Traccia title, which `(combo, famiglia)` of `output.inviluppo` achieves it.

`A_s` is computed in mm² (M_Ed·10⁶ converts the kNm Valore to N·mm, the unit `flessione.
_as_required_cm2` itself works in) and displayed in cm² via `scala` (docs §2/§3: never hide the
mm²->cm² conversion inside a folded constant)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .flessione import MARGIN_EFFECTIVE_DEPTH_MM, MINIMUM_REINFORCEMENT_RATIO, TWO_FACES, mead_families
from .input import PlintoIsolatoInput
from .inviluppo import InviluppoRiga
from .models import PlintoIsolatoOutput

NMM_PER_KNM = 1_000_000.0  # unit conversion: M_Ed's own Valore is given in kNm, the formula needs N*mm.
MM2_PER_CM2 = 100.0  # display factor mm2 -> cm2 (docs/architecture-phase2.md §2 "scala").
BRACCIO_DI_LEVA = 0.9  # braccio di leva approssimato z = 0.9*d.
CLAUSOLA_ARMATURA = "NTC2018 §4.1.2"
CLAUSOLA_AS_MIN = "NTC2018 §4.1.6.1.1"


def traccia_momento_e_armatura(inputs: PlintoIsolatoInput, output: PlintoIsolatoOutput) -> Traccia:
    """d + mensola X/Y + armatura richiesta X/Y (con A_s,min e area governante), dalla pressione
    governante sulle famiglie ULS."""
    famiglie = mead_families(legacy_compat=False)
    entry = _riga_slu_governante(output.inviluppo, famiglie)
    sigma_slu = entry.valore if entry is not None else 0.0
    h_mm = inputs.h_plinto_m * 1000.0
    fyd = output.materiali.acciaio.fyd_MPa

    passo_d = _passo_d(inputs, h_mm)
    mx_passo = _passo_momento(inputs, sigma_slu, output.flessione.mx_slu_kNm, direzione="X")
    my_passo = _passo_momento(inputs, sigma_slu, output.flessione.my_slu_kNm, direzione="Y")
    as_x_passo = _passo_armatura(mx_passo, passo_d.risultato, fyd, output.flessione.as_x_cm2, direzione="X")
    as_y_passo = _passo_armatura(my_passo, passo_d.risultato, fyd, output.flessione.as_y_cm2, direzione="Y")
    as_x_min_passo = _passo_as_min(inputs.by_m * 1000.0, h_mm, output.flessione.as_x_min_cm2, direzione="X")
    as_y_min_passo = _passo_as_min(inputs.ax_m * 1000.0, h_mm, output.flessione.as_y_min_cm2, direzione="Y")
    passi = (
        passo_d,
        mx_passo, as_x_passo, as_x_min_passo, _passo_as_governante(as_x_passo, as_x_min_passo, direzione="X"),
        my_passo, as_y_passo, as_y_min_passo, _passo_as_governante(as_y_passo, as_y_min_passo, direzione="Y"),
    )
    titolo = _titolo(entry)
    return Traccia(titolo=titolo, passi=passi)


def _passo_d(inputs: PlintoIsolatoInput, h_mm: float) -> Passo:
    """Review finding (MISSING_STEP): d entrava nella formula dell'armatura richiesta senza un
    passo che lo derivasse da H/copriferro/margine (come si è fatto in ca_travi)."""
    c_mm = inputs.copriferro_cm * 10.0
    return Passo(
        simbolo="d", formula=f"H - c - {MARGIN_EFFECTIVE_DEPTH_MM:g}",
        valori=(
            Valore(simbolo="H", valore=h_mm, unita="mm", descrizione="altezza del plinto"),
            Valore(simbolo="c", valore=c_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=h_mm - c_mm - MARGIN_EFFECTIVE_DEPTH_MM, unita="mm",
        nota="Altezza utile della sezione, con margine φ/2 assunto (mezzo diametro di riferimento, "
             "prima della scelta del diametro effettivo, che dipende dall'area di armatura).",
    )


def _passo_as_min(larghezza_mm: float, h_mm: float, risultato: float, *, direzione: str) -> Passo:
    """Review finding (MISSING_STEP): A_s,min (piastra/soletta, entrambe le facce) non compariva
    mai nella traccia."""
    simbolo = f"A_s,{direzione.lower()},min"
    simbolo_larghezza = "B_Y" if direzione == "X" else "A_X"
    return Passo(
        simbolo=simbolo, formula=f"{TWO_FACES:g} * {MINIMUM_REINFORCEMENT_RATIO:g} * {simbolo_larghezza} * H",
        valori=(
            Valore(simbolo=simbolo_larghezza, valore=larghezza_mm, unita="mm"),
            Valore(simbolo="H", valore=h_mm, unita="mm"),
        ),
        risultato=risultato, unita="cm2", scala=1.0 / MM2_PER_CM2, clausola=CLAUSOLA_AS_MIN,
        nota="Armatura minima di piastra/soletta, 0,1% su entrambe le facce.",
    )


def _passo_as_governante(passo_as: Passo, passo_as_min: Passo, *, direzione: str) -> Passo:
    """Review finding (MISSING_STEP): il passo di scelta max(A_s, A_s,min), da cui deriva il
    diametro/passo effettivamente adottato (`flessione._phi_richiesto_mm`), non compariva mai."""
    simbolo = f"A_s,{direzione.lower()},gov"
    return Passo(
        simbolo=simbolo, formula=f"max({passo_as.simbolo}, {passo_as_min.simbolo})",
        valori=(
            Valore(simbolo=passo_as.simbolo, valore=passo_as.risultato, unita="cm2"),
            Valore(simbolo=passo_as_min.simbolo, valore=passo_as_min.risultato, unita="cm2"),
        ),
        risultato=max(passo_as.risultato, passo_as_min.risultato), unita="cm2",
        nota="Area di armatura governante fra calcolo e minimo; il diametro/passo adottato arrotonda "
             "quest'area al diametro commerciale superiore (φ_x/φ_y in output).",
    )


def _riga_slu_governante(inviluppo: tuple[InviluppoRiga, ...], famiglie: tuple[str, ...]) -> InviluppoRiga | None:
    candidati = [r for r in inviluppo if r.grandezza == "pressione_max_kpa" and r.famiglia in famiglie]
    return max(candidati, key=lambda r: r.valore) if candidati else None


def _titolo(entry: InviluppoRiga | None) -> str:
    if entry is None:
        return "Momento a sbalzo e armatura richiesta — nessuna combinazione ULS presente (σ_SLU = 0)"
    return f"Momento a sbalzo e armatura richiesta — combinazione governante {entry.combo} ({entry.famiglia})"


def _passo_momento(inputs: PlintoIsolatoInput, sigma_slu: float, risultato: float, *, direzione: str) -> Passo:
    if direzione == "X":
        simbolo, luce, larghezza, semi_pedestal, extra = "M_x,SLU", inputs.ax_m, inputs.by_m, inputs.a_pedestal_m, inputs.ex_m
        simbolo_luce, simbolo_larghezza, simbolo_semi_pedestal, simbolo_extra = "A_X", "B_Y", "a_X", "e_X,appl"
    else:
        simbolo, luce, larghezza, semi_pedestal, extra = "M_y,SLU", inputs.by_m, inputs.ax_m, inputs.b_pedestal_m, inputs.ey_m
        simbolo_luce, simbolo_larghezza, simbolo_semi_pedestal, simbolo_extra = "B_Y", "A_X", "a_Y", "e_Y,appl"
    formula = (f"σ_SLU * {simbolo_larghezza} * "
               f"(max({simbolo_luce}/2 - {simbolo_semi_pedestal}/2, 0) + {simbolo_extra})^2 / 2")
    return Passo(
        simbolo=simbolo, formula=formula,
        valori=(
            Valore(simbolo="σ_SLU", valore=sigma_slu, unita="kPa", descrizione="pressione massima sulle famiglie ULS (SLU_STR/SLU_EQU/SLV_STR/SLV_EQU)"),
            Valore(simbolo=simbolo_larghezza, valore=larghezza, unita="m"),
            Valore(simbolo=simbolo_luce, valore=luce, unita="m"),
            Valore(simbolo=simbolo_semi_pedestal, valore=semi_pedestal, unita="m", descrizione="dimensione del bicchiere sull'asse della mensola"),
            Valore(simbolo=simbolo_extra, valore=extra, unita="m", descrizione="eccentricità di carico applicata"),
        ),
        risultato=risultato, unita="kNm",
        nota="Momento flettente a sbalzo dal filo del pilastro/bicchiere, per una striscia di larghezza unitaria integrata sulla larghezza del plinto.",
    )


def _passo_armatura(passo_momento: Passo, d_mm: float, fyd_MPa: float, risultato: float, *, direzione: str) -> Passo:
    simbolo = "A_s,x" if direzione == "X" else "A_s,y"
    return Passo(
        simbolo=simbolo, formula=f"{NMM_PER_KNM:.0f} * {passo_momento.simbolo} / ({BRACCIO_DI_LEVA:g} * d * f_yd)",
        valori=(
            Valore(simbolo=passo_momento.simbolo, valore=passo_momento.risultato, unita="kNm"),
            Valore(simbolo="d", valore=d_mm, unita="mm", descrizione="altezza utile della sezione (H - copriferro - mezzo diametro)"),
            Valore(simbolo="f_yd", valore=fyd_MPa, unita="MPa"),
        ),
        risultato=risultato, unita="cm2", scala=1.0 / MM2_PER_CM2, clausola=CLAUSOLA_ARMATURA,
        nota="Armatura richiesta con braccio di leva approssimato z = 0,9·d.",
    )

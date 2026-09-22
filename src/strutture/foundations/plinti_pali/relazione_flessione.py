"""Verified restatement (docs/architecture-phase2.md §6) of Tool-2's bottom flexural design
(`flessione.py`, EC2 §9.3.1.1): governing bending moment (beam-on-pile-rows analogy), internal
lever arm `z` (rectangular-section equilibrium, capped at the balanced-section limit) and required
bottom reinforcement, direction X-X fully derived, direction Y-Y restated compactly with the SAME
method (mirrors how `ca_travi.relazione_geometria` derives `z` once and reuses it — here the reuse
is across the two orthogonal directions instead of across later Tracce).

`Mu`'s own case selection (`_mu_dati`, mirrors `flessione._mu_inferiore`/`_mu_beam`) and `z`'s own
cap (`_z_mm`, mirrors `flessione._braccio_leva_mm`) are restated INLINE rather than importing the
package's private helpers (`_mu_beam`/`_braccio_leva_mm`), the same convention `plinti_isolati.
relazione_azioni` documents for its own inlined `azioni_base()`/`eccentricities()`. `n_barre_per_m`
(from `passo_mm` via `ceil`) is cited directly from the output: `ceil` is not in the notation
grammar's function whitelist (docs/architecture-phase2.md §2), the same gap `sle_tensioni`'s table
lookups hit in `ca_travi.relazione_sle`."""
import math

from strutture.shared.numeric import clamp
from strutture.shared.relazione import Passo, Traccia, Valore

from .flessione import AS_MIN_RATIO_INF, MARGIN_LEVER_ARM, MU_ADIMENSIONALE_MAX, STRIP_WIDTH_MM
from .input import PlintoSuPaliInput
from .inviluppo import InviluppoRiga
from .models import PlintoSuPaliOutput
from .models_flessione import DesignFlessione
from .relazione_comune import fcd_frammento, valore_fck, valore_fyd, valore_gamma_c
from .relazione_helpers import mu_beam, trova_riga
from .rows import RigaCarico
from .schema import grid_counts

EC2_ARMATURA_MINIMA = "EC2 §9.3.1.1"


def traccia_flessione_x(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, peso_kN: float) -> Traccia:
    """5 passi, direzione X-X: M_u, d, z, A_s,prov, Check "Armatura inferiore X-X"."""
    per_grandezza = {r.grandezza: r for r in output.inviluppo}
    count_x, count_y = grid_counts(inputs.schema_pali)
    mu_kNm, n_eff, m_assoc, combo, nodo = _mu_dati(output.righe, per_grandezza, count_x, count_y, inputs.lx_m, peso_kN, asse="x")
    h_mm, c_mm = inputs.h_plinto_m * 1000.0, inputs.copriferro_cm * 10.0
    inf_x = output.flessione.inf_x
    fyd_MPa = output.materiali.acciaio.fyd_MPa
    d_mm = h_mm - c_mm - MARGIN_LEVER_ARM * inputs.diametro_inf_x_mm
    fcd_MPa = 0.85 * output.materiali.calcestruzzo.fck_MPa / inputs.gamma_c
    z_mm = _z_mm(mu_kNm, d_mm, fcd_MPa)
    passi = (
        _passo_mu("X", count_x, count_y, inputs.lx_m, "L_X", mu_kNm, n_eff, m_assoc, combo),
        _passo_d("X", h_mm, c_mm, inputs.diametro_inf_x_mm, d_mm),
        _passo_z("X", mu_kNm, d_mm, inputs.gamma_c, output.materiali.calcestruzzo.fck_MPa, z_mm),
        _passo_as_prov("X", inf_x),
        _passo_check_armatura("X", "M_u,X", "z_X", "H", h_mm, fyd_MPa, inf_x, EC2_ARMATURA_MINIMA, z_mm=z_mm),
    )
    titolo = f"Flessione della soletta e armatura inferiore — direzione X-X — combinazione governante {combo} (nodo {nodo})"
    return Traccia(titolo=titolo, passi=passi)


def traccia_flessione_y(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, peso_kN: float) -> Traccia:
    """2 passi (forma compatta, stesso procedimento della direzione X-X): M_u,Y, Check "Armatura
    inferiore Y-Y" (z_Y/d_Y/A_s,prov,Y come Valore con descrizione, non passi propri — la
    derivazione è già mostrata per esteso sopra)."""
    per_grandezza = {r.grandezza: r for r in output.inviluppo}
    count_x, count_y = grid_counts(inputs.schema_pali)
    mu_kNm, n_eff, m_assoc, combo, nodo = _mu_dati(output.righe, per_grandezza, count_y, count_x, inputs.ly_m, peso_kN, asse="y")
    h_mm, c_mm = inputs.h_plinto_m * 1000.0, inputs.copriferro_cm * 10.0
    inf_y = output.flessione.inf_y
    fyd_MPa = output.materiali.acciaio.fyd_MPa
    d_mm = h_mm - c_mm - MARGIN_LEVER_ARM * inputs.diametro_inf_y_mm
    fcd_MPa = 0.85 * output.materiali.calcestruzzo.fck_MPa / inputs.gamma_c
    z_mm = _z_mm(mu_kNm, d_mm, fcd_MPa)
    z_nota = (
        f"braccio di leva interno, stessa formula di z_X sopra (d_Y={d_mm:.0f} mm da "
        f"H − c − {MARGIN_LEVER_ARM:g}·φ_Y, φ_Y={inputs.diametro_inf_y_mm:g} mm)"
    )
    passi = (
        _passo_mu("Y", count_y, count_x, inputs.ly_m, "L_Y", mu_kNm, n_eff, m_assoc, combo),
        _passo_check_armatura("Y", "M_u,Y", "z_Y", "H_Y", h_mm, fyd_MPa, inf_y, EC2_ARMATURA_MINIMA, z_mm=z_mm, z_nota=z_nota),
    )
    titolo = f"Flessione della soletta e armatura inferiore — direzione Y-Y — combinazione governante {combo} (nodo {nodo})"
    return Traccia(titolo=titolo, passi=passi)


def _mu_dati(
    righe: tuple[RigaCarico, ...], per_grandezza: dict[str, InviluppoRiga],
    n_own: int, n_perp: int, spacing_m: float, peso_kN: float, *, asse: str,
) -> tuple[float, float, float, str, int]:
    """Mirrors `flessione._mu_inferiore`: (Mu, N_eff, M_assoc, combo, nodo) of whichever of case A
    (N totale massimo) / case B (momento estremo) governs.

    Review finding (MISLEADING): né questa Traccia né "Reazioni sui pali" dichiaravano la
    combinazione/nodo governante l'una rispetto all'altra (§5 dell'architettura richiede che un
    tool a molte righe nomini SEMPRE la riga governante nel titolo della Traccia) — `nodo` è ora
    restituito e usato per completare il titolo insieme a `combo`."""
    m_assoc_attr = "my_finale_kNm" if asse == "x" else "mx_finale_kNm"
    massimo, minimo = (per_grandezza["my_max"], per_grandezza["my_min"]) if asse == "x" else (per_grandezza["mx_max"], per_grandezza["mx_min"])

    riga_totale_max = per_grandezza["n_totale_max"]
    riga_a = trova_riga(righe, riga_totale_max.nodo, riga_totale_max.combo)
    n_a, m_a = riga_totale_max.valore + peso_kN, getattr(riga_a, m_assoc_attr)
    mu_a = mu_beam(n_own, n_perp, spacing_m, n_a, m_a)

    usa_massimo = massimo.valore > abs(minimo.valore)
    scelta = massimo if usa_massimo else minimo
    riga_b = trova_riga(righe, scelta.nodo, scelta.combo)
    n_b, m_b = riga_b.n_kN + peso_kN, max(massimo.valore, abs(minimo.valore))
    mu_b = mu_beam(n_own, n_perp, spacing_m, n_b, m_b)

    if mu_b >= mu_a:
        return mu_b, n_b, m_b, scelta.combo, scelta.nodo
    return mu_a, n_a, m_a, riga_totale_max.combo, riga_totale_max.nodo


def _z_mm(mu_kNm: float, d_mm: float, fcd_MPa: float) -> float:
    """Mirrors `flessione._braccio_leva_mm` (standard-mode branch only)."""
    if mu_kNm <= 0.0:
        return d_mm
    mu_adim = clamp(mu_kNm * 1.0e6 / (STRIP_WIDTH_MM * d_mm**2 * fcd_MPa), 0.0, MU_ADIMENSIONALE_MAX)
    return d_mm * (0.5 + math.sqrt(0.25 - mu_adim))


def _passo_mu(
    direzione: str, n_own: int, n_perp: int, spacing_m: float, spacing_simbolo: str,
    mu_kNm: float, n_eff: float, m_assoc: float, combo: str,
) -> Passo:
    """Review finding (MISLEADING): "N" qui è `env.n_totale_max`/`riga[m_max].n_kN` PIÙ il peso
    proprio del plinto — una combinazione E un aggregato diversi dal semplice carico di colonna "N"
    di "Reazioni sui pali" (quello, invece, è la sola reazione della combinazione governante lì).
    Il simbolo "N_tot,W" (N totale inviluppato + peso proprio W) distingue le due grandezze a
    colpo d'occhio, come `muro.relazione_armatura_fondazione` fa con "A_s,nec (paramento)"."""
    m_simbolo = "M_y" if direzione == "X" else "M_x"
    if n_own == 1:
        formula = f"abs({m_simbolo})"
        valori = (Valore(simbolo=m_simbolo, valore=m_assoc, unita="kNm", descrizione=f"momento associato, combinazione governante {combo}"),)
        nota = "Direzione con una sola fila di pali: trasferimento diretto del momento, nessuna azione a trave."
    else:
        fattore = 0.5 if n_perp >= 2 else 1.0
        formula = f"{fattore:g} * N_tot,W * {spacing_simbolo} / 4 + abs({m_simbolo})"
        valori = (
            Valore(simbolo="N_tot,W", valore=n_eff, unita="kN",
                   descrizione=f"carico totale in colonna (inviluppo) più il peso proprio del plinto, combinazione governante {combo}"),
            Valore(simbolo=spacing_simbolo, valore=spacing_m, unita="m", descrizione="interasse dei pali in questa direzione"),
            Valore(simbolo=m_simbolo, valore=m_assoc, unita="kNm", descrizione=f"momento associato, combinazione governante {combo}"),
        )
        nota = f"{fattore:g} = quota di carico assegnata alla fascia (0,5 se ripartita su due file di pali, 1,0 se su una sola)."
    return Passo(simbolo=f"M_u,{direzione}", formula=formula, valori=valori, risultato=mu_kNm, unita="kNm", nota=nota)


def _passo_d(direzione: str, h_mm: float, c_mm: float, diametro_mm: float, d_mm: float) -> Passo:
    return Passo(
        simbolo=f"d_{direzione}", formula=f"H - c - {MARGIN_LEVER_ARM:g} * φ_{direzione}",
        valori=(
            Valore(simbolo="H", valore=h_mm, unita="mm", descrizione="altezza del plinto (input in m, qui in mm)"),
            Valore(simbolo="c", valore=c_mm, unita="mm", descrizione="copriferro netto (input in cm, qui in mm)"),
            Valore(simbolo=f"φ_{direzione}", valore=diametro_mm, unita="mm", descrizione=f"diametro dell'armatura inferiore, direzione {direzione}-{direzione}"),
        ),
        risultato=d_mm, unita="mm",
        nota="Altezza utile della fascia da 1 m, con margine convenzionale di 1,5 diametri (non l'asse della barra).",
    )


def _passo_z(direzione: str, mu_kNm: float, d_mm: float, gamma_c: float, fck_MPa: float, z_mm: float) -> Passo:
    d_simbolo = f"d_{direzione}"
    formula = (
        f"{d_simbolo} * (0.5 + sqrt(0.25 - min(max(M_u,{direzione} * 1e6 / "
        f"(1000 * {d_simbolo}^2 * {fcd_frammento()}), 0), 0.25)))"
    )
    return Passo(
        simbolo=f"z_{direzione}", formula=formula,
        valori=(
            Valore(simbolo=f"M_u,{direzione}", valore=mu_kNm, unita="kNm", descrizione="momento flettente di progetto, calcolato sopra"),
            Valore(simbolo=d_simbolo, valore=d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            valore_fck(fck_MPa), valore_gamma_c(gamma_c),
        ),
        risultato=z_mm, unita="mm", clausola="EN 1992-1-1 §6.1",
        nota="Braccio di leva interno dall'equilibrio a rottura della sezione rettangolare, limitato al "
             "valore di sezione bilanciata (mu ≤ 0,25) così l'armatura non risulta mai sottostimata.",
    )


def _passo_as_prov(direzione: str, design: DesignFlessione) -> Passo:
    return Passo(
        simbolo=f"A_s,prov,{direzione}", formula=f"n_{direzione} * π * φ_{direzione}^2 / 4",
        valori=(
            Valore(simbolo=f"n_{direzione}", valore=float(design.n_barre_per_m), descrizione=f"barre per metro, arrotondamento per eccesso di 1000/passo_inf_{direzione}"),
            Valore(simbolo="π", valore=math.pi),
            Valore(simbolo=f"φ_{direzione}", valore=design.diametro_mm, unita="mm"),
        ),
        risultato=design.as_prov_mm2, unita="mm2/m",
        nota=f"Armatura inferiore {direzione}-{direzione} effettivamente disposta (⌀{design.diametro_mm:g}/{design.passo_mm:g}).",
    )


def _passo_check_armatura(
    direzione: str, mu_simbolo: str, z_simbolo: str, h_simbolo: str, h_mm: float, fyd_MPa: float,
    design: DesignFlessione, clausola: str, *, z_mm: float, z_nota: str = "",
) -> Passo:
    formula = f"max({mu_simbolo} * 1e6 / ({z_simbolo} * f_yd), {AS_MIN_RATIO_INF:g} * 1000 * {h_simbolo}) <= A_s,prov,{direzione}"
    valori = (
        Valore(simbolo=mu_simbolo, valore=design.mu_kNm, unita="kNm", descrizione="momento flettente di progetto, calcolato sopra"),
        Valore(simbolo=z_simbolo, valore=z_mm, unita="mm", descrizione=z_nota or "braccio di leva interno, calcolato sopra"),
        valore_fyd(fyd_MPa),
        Valore(simbolo=h_simbolo, valore=h_mm, unita="mm", descrizione="altezza del plinto, in mm"),
        Valore(simbolo=f"A_s,prov,{direzione}", valore=design.as_prov_mm2, unita="mm2/m",
               descrizione=f"armatura {direzione}-{direzione} disposta (⌀{design.diametro_mm:g}/{design.passo_mm:g})"),
    )
    return Passo(
        simbolo=f"A_s,req,{direzione}", formula=formula, valori=valori,
        risultato=design.as_req_mm2, unita="mm2/m", clausola=clausola,
        esito="soddisfatta" if design.verificato else "non soddisfatta",
        nota="Progetto a striscia di 1 m come nel foglio: M_u è il momento dell'intera fascia di pali, mentre z, "
             f"A_s,min ({AS_MIN_RATIO_INF * 100:g}% dell'area lorda) e A_s,prov sono per metro — a favore di sicurezza "
             "di circa la larghezza del plinto in metri (registro: plinti-pali/flessione-soletta-momento-di-fascia-su-striscia-di-1-m).",
    )

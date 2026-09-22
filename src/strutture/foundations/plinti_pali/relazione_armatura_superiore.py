"""Verified restatement (docs/architecture-phase2.md §6) of Tool-2's top ("sup") reinforcement
block (`flessione._mu_superiore`): the uplift-governed bending moment that sizes the top bars.
Informative only — `models_flessione.py`'s own docstring says this block is "a simplified secondary
check, not surfaced in `Per Relazione`" (`tool.py::_checks` has no Check for it), so neither Passo
below carries an `esito` (lesson: an informative value that is NOT a normative check must say so)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .input import PlintoSuPaliInput
from .inviluppo import InviluppoRiga
from .models import PlintoSuPaliOutput
from .models_flessione import DesignFlessione
from .relazione_helpers import mu_beam, trova_riga
from .rows import RigaCarico
from .schema import grid_counts


def traccia_armatura_superiore(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> Traccia:
    """2 passi informativi: M_u,sup nelle due direzioni (armatura superiore di progetto: ⌀ e passo
    dell'armatura disposta sono richiamati nella nota, non è un Check normativo del report)."""
    per_grandezza = {r.grandezza: r for r in output.inviluppo}
    count_x, count_y = grid_counts(inputs.schema_pali)
    passi = (
        _passo_mu_sup("X", output.righe, per_grandezza, count_x, count_y, inputs.lx_m, output.flessione.sup_x, "my_finale_kNm"),
        _passo_mu_sup("Y", output.righe, per_grandezza, count_y, count_x, inputs.ly_m, output.flessione.sup_y, "mx_finale_kNm"),
    )
    return Traccia(titolo="Armatura superiore (verifica secondaria semplificata)", passi=passi)


def _passo_mu_sup(
    direzione: str, righe: tuple[RigaCarico, ...], per_grandezza: dict[str, InviluppoRiga],
    n_own: int, n_perp: int, spacing_m: float, design: DesignFlessione, campo_momento: str,
) -> Passo:
    n_totale_min = per_grandezza["n_totale_min"]
    riga = trova_riga(righe, n_totale_min.nodo, n_totale_min.combo)
    n_top = -n_totale_min.valore
    m_assoc = getattr(riga, campo_momento)
    m_simbolo = "M_y" if direzione == "X" else "M_x"
    mu_sup = abs(mu_beam(n_own, n_perp, spacing_m, n_top, m_assoc))
    nota = (
        f"Momento di progetto per l'armatura superiore (verifica secondaria, non un Check del report); "
        f"disposta ⌀{design.diametro_mm:g}/{design.passo_mm:g} (As,prov={design.as_prov_mm2:.0f} mm²/m)."
    )
    if n_own == 1:
        formula, valori = f"abs({m_simbolo})", (
            Valore(simbolo=m_simbolo, valore=m_assoc, unita="kNm", descrizione="momento associato alla combinazione di sollevamento"),
        )
    else:
        fattore = 0.5 if n_perp >= 2 else 1.0
        spacing_simbolo = f"L_{direzione}"
        formula = f"abs({fattore:g} * N_top * {spacing_simbolo} / 4 + {m_simbolo})"
        valori = (
            Valore(simbolo="N_top", valore=n_top, unita="kN", descrizione=f"reazione di sollevamento (N totale minimo negato), combinazione {n_totale_min.combo}"),
            Valore(simbolo=spacing_simbolo, valore=spacing_m, unita="m", descrizione="interasse dei pali in questa direzione"),
            Valore(simbolo=m_simbolo, valore=m_assoc, unita="kNm", descrizione="momento associato alla stessa combinazione"),
        )
    return Passo(simbolo=f"M_u,sup,{direzione}", formula=formula, valori=valori, risultato=mu_sup, unita="kNm", nota=nota)

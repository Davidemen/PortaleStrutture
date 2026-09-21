"""`relazione.py` (docs/architecture-phase2.md §6): self-weights, base actions and contact
pressure of the SIGMA-GOVERNING row (`output.governante`, the combination that maximises
`sigma_max_kpa` across every famiglia — `tool.py::run`'s own `governing(..., "max")`). The
self-weight components come straight from `pesi_propri()` (this package's own step function);
`N`/the eccentricities restate `azioni_base()`/`footing_pressure.eccentricities()` inline (both
closed-form) rather than re-importing them, to keep one Passo per displayed line.

The base-pressure formula (Navier, `σ = N/A·(1 ± 6·e/b)`) is exact for BOTH `metodo_pressioni`
options only while the row is fully compressed (`compressed_ratio == 1`, see `shared.footing_
pressure.biaxial_navier`/`sovrapposizione`: out of kern, the exact method solves a no-tension
plane numerically — no closed form to restate). `_verifica_interamente_compressa` raises for a
partially-compressed governing row so the trace degrades to "non disponibile" (docs §1) instead of
silently restating the wrong formula."""
from strutture.shared.load_table import ReactionRow
from strutture.shared.relazione import Passo, Traccia, Valore

from .checks_inviluppo import BEARING_CLAUSE
from .gamma_azioni import GAMMA_EQU, GAMMA_SISMICA, GAMMA_STR, gamma_permanenti
from .input import PlintoIsolatoInput
from .legacy_units import sigma_ammissibile_kpa
from .pesi_propri import GAMMA_CALCESTRUZZO_KNM3, PesiPropri, pesi_propri
from .riga_verifica import RigaVerifica
from .rows import ResistenzaRow

NTC_TAB_2_6_I = "NTC2018 Tab. 2.6.I"
NTC_PORTANZA_NAVIER = "NTC2018 §6.4.2.1"
_GAMMA_W_NOTE: dict[float, str] = {
    GAMMA_STR: "combinazione STR, carichi permanenti sfavorevoli (Tab. 2.6.I, A1)",
    GAMMA_EQU: "combinazione EQU, peso proprio stabilizzante (Tab. 2.6.I, EQU)",
    GAMMA_SISMICA: "combinazione sismica o di esercizio, γG = γQ = 1 (NTC2018 §2.5.3)",
}


def traccia_pesi_propri_e_carico(
    inputs: PlintoIsolatoInput, riga: RigaVerifica, reazione: ReactionRow,
) -> Traccia:
    """Self-weight of plinth/pedestal/soil cover + total factored vertical load N, for `riga`."""
    pesi = pesi_propri(
        inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.h_interro_m,
        inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.h_pedestal_sopra_m, inputs.h_pedestal_sotto_m,
        inputs.gamma_terreno_kNm3,
    )
    passi = (_passo_w_plinto(inputs, pesi),)
    if inputs.a_pedestal_m > 0 or inputs.b_pedestal_m > 0:
        passi = (*passi, _passo_w_pedestal(inputs, pesi))
    passi = (*passi, _passo_w_terreno(inputs, pesi), _passo_n(inputs, reazione, pesi, riga))
    titolo = f"Pesi propri e carico verticale — combinazione governante {riga.combo} ({riga.famiglia})"
    return Traccia(titolo=titolo, passi=passi)


def _passo_w_plinto(inputs: PlintoIsolatoInput, pesi: PesiPropri) -> Passo:
    return Passo(
        simbolo="W_plinto", formula=f"A_X * B_Y * H * {GAMMA_CALCESTRUZZO_KNM3:g}",
        valori=(
            Valore(simbolo="A_X", valore=inputs.ax_m, unita="m", descrizione="dimensione in pianta lungo X"),
            Valore(simbolo="B_Y", valore=inputs.by_m, unita="m", descrizione="dimensione in pianta lungo Y"),
            Valore(simbolo="H", valore=inputs.h_plinto_m, unita="m", descrizione="altezza del plinto"),
        ),
        risultato=pesi.w_plinto_kN, unita="kN",
        nota=f"γ_cls = {GAMMA_CALCESTRUZZO_KNM3:g} kN/m³, peso di volume del calcestruzzo armato.",
    )


def _passo_w_pedestal(inputs: PlintoIsolatoInput, pesi: PesiPropri) -> Passo:
    return Passo(
        simbolo="W_bicchiere", formula=f"a_X * a_Y * (s_sup + s_inf) * {GAMMA_CALCESTRUZZO_KNM3:g}",
        valori=(
            Valore(simbolo="a_X", valore=inputs.a_pedestal_m, unita="m", descrizione="dimensione del bicchiere lungo X"),
            Valore(simbolo="a_Y", valore=inputs.b_pedestal_m, unita="m", descrizione="dimensione del bicchiere lungo Y"),
            Valore(simbolo="s_sup", valore=inputs.h_pedestal_sopra_m, unita="m", descrizione="altezza del bicchiere sopra il piano campagna"),
            Valore(simbolo="s_inf", valore=inputs.h_pedestal_sotto_m, unita="m", descrizione="altezza del bicchiere sotto il piano campagna"),
        ),
        risultato=pesi.w_pedestal_kN, unita="kN",
    )


def _passo_w_terreno(inputs: PlintoIsolatoInput, pesi: PesiPropri) -> Passo:
    return Passo(
        simbolo="W_terreno", formula="(A_X * B_Y - a_X * a_Y) * h * γ",
        valori=(
            Valore(simbolo="A_X", valore=inputs.ax_m, unita="m"),
            Valore(simbolo="B_Y", valore=inputs.by_m, unita="m"),
            Valore(simbolo="a_X", valore=inputs.a_pedestal_m, unita="m", descrizione="dimensione del bicchiere lungo X"),
            Valore(simbolo="a_Y", valore=inputs.b_pedestal_m, unita="m", descrizione="dimensione del bicchiere lungo Y"),
            Valore(simbolo="h", valore=inputs.h_interro_m, unita="m", descrizione="profondità di ricoprimento"),
            Valore(simbolo="γ", valore=inputs.gamma_terreno_kNm3, unita="kN/m3", descrizione="peso di volume del terreno di ricoprimento"),
        ),
        risultato=pesi.w_terreno_kN, unita="kN",
    )


def _passo_n(inputs: PlintoIsolatoInput, reazione: ReactionRow, pesi: PesiPropri, riga: RigaVerifica) -> Passo:
    gamma_w = gamma_permanenti(riga.famiglia, legacy_compat=False)
    return Passo(
        simbolo="N", formula="F_z + (W_plinto + W_bicchiere + W_terreno) * γ_G",
        valori=(
            Valore(simbolo="F_z", valore=reazione.fz_kN, unita="kN", descrizione=f"reazione verticale, nodo {reazione.nodo}, {reazione.combo}"),
            Valore(simbolo="W_plinto", valore=pesi.w_plinto_kN, unita="kN"),
            Valore(simbolo="W_bicchiere", valore=pesi.w_pedestal_kN, unita="kN"),
            Valore(simbolo="W_terreno", valore=pesi.w_terreno_kN, unita="kN"),
            Valore(simbolo="γ_G", valore=gamma_w, descrizione=_GAMMA_W_NOTE[gamma_w]),
        ),
        risultato=riga.n_kN, unita="kN", clausola=NTC_TAB_2_6_I,
        nota="Carico verticale totale alla base, dopo l'aggiunta dei pesi propri fattorizzati.",
    )


def traccia_eccentricita_e_pressioni(
    inputs: PlintoIsolatoInput, riga: RigaVerifica, reazione: ReactionRow,
) -> Traccia:
    """Base eccentricities, contact pressure extremes and the "Portanza" check of `riga` (the
    sigma-governing row). Raises `ValueError` if `riga` is not fully compressed (see module
    docstring)."""
    _verifica_interamente_compressa(riga)
    passi = (
        _passo_ex(inputs, reazione, riga),
        _passo_ey(inputs, reazione, riga),
        _passo_sigma_max(inputs, riga),
        _passo_sigma_min(inputs, riga),
        _passo_verifica_portanza(inputs, riga),
    )
    titolo = f"Eccentricità e pressioni di contatto — combinazione governante {riga.combo} ({riga.famiglia})"
    return Traccia(titolo=titolo, passi=passi)


def _verifica_interamente_compressa(riga: RigaVerifica) -> None:
    if riga.compressed_ratio != 1.0:
        raise ValueError(
            f"combinazione '{riga.combo}' (nodo {riga.nodo}): base parzializzata "
            f"(compressed_ratio={riga.compressed_ratio:g}), la formula di Navier non è esatta "
            "fuori dal nocciolo d'inerzia."
        )


def _passo_ex(inputs: PlintoIsolatoInput, reazione: ReactionRow, riga: RigaVerifica) -> Passo:
    leva_m = inputs.h_plinto_m + inputs.offset_leva_m
    return Passo(
        simbolo="e_X", formula="(abs(M_y) + abs(F_x) * (H + s) + N * e_X,appl) / N",
        valori=(
            Valore(simbolo="M_y", valore=reazione.my_kNm, unita="kNm", descrizione="momento My alla sommità del pilastro"),
            Valore(simbolo="F_x", valore=reazione.fx_kN, unita="kN", descrizione="taglio Fx alla sommità del pilastro"),
            Valore(simbolo="H", valore=inputs.h_plinto_m, unita="m"),
            Valore(simbolo="s", valore=inputs.offset_leva_m, unita="m", descrizione="offset del braccio di leva"),
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="e_X,appl", valore=inputs.ex_m, unita="m", descrizione="eccentricità di carico applicata lungo X"),
        ),
        risultato=riga.ex_m, unita="m",
        nota=f"Myy = |M_y| + |F_x|·(H+s) + N·e_X,appl = {leva_m:g}·|F_x| + N·e_X,appl + |M_y|; e_X = Myy/N.",
    )


def _passo_ey(inputs: PlintoIsolatoInput, reazione: ReactionRow, riga: RigaVerifica) -> Passo:
    return Passo(
        simbolo="e_Y", formula="(abs(M_x) + abs(F_y) * (H + s) + N * e_Y,appl) / N",
        valori=(
            Valore(simbolo="M_x", valore=reazione.mx_kNm, unita="kNm", descrizione="momento Mx alla sommità del pilastro"),
            Valore(simbolo="F_y", valore=reazione.fy_kN, unita="kN", descrizione="taglio Fy alla sommità del pilastro"),
            Valore(simbolo="H", valore=inputs.h_plinto_m, unita="m"),
            Valore(simbolo="s", valore=inputs.offset_leva_m, unita="m", descrizione="offset del braccio di leva"),
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="e_Y,appl", valore=inputs.ey_m, unita="m", descrizione="eccentricità di carico applicata lungo Y"),
        ),
        risultato=riga.ey_m, unita="m",
        nota="Mxx = |M_x| + |F_y|·(H+s) + N·e_Y,appl; e_Y = Mxx/N.",
    )


def _passo_sigma_max(inputs: PlintoIsolatoInput, riga: RigaVerifica) -> Passo:
    return Passo(
        simbolo="σ_max", formula="N / (A_X * B_Y) * (1 + 6 * abs(e_X) / A_X + 6 * abs(e_Y) / B_Y)",
        valori=(
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="A_X", valore=inputs.ax_m, unita="m"),
            Valore(simbolo="B_Y", valore=inputs.by_m, unita="m"),
            Valore(simbolo="e_X", valore=riga.ex_m, unita="m"),
            Valore(simbolo="e_Y", valore=riga.ey_m, unita="m"),
        ),
        risultato=riga.sigma_max_kpa, unita="kPa", clausola=NTC_PORTANZA_NAVIER,
        nota="Formula di Navier per base rigida rettangolare, valida per base interamente compressa.",
    )


def _passo_sigma_min(inputs: PlintoIsolatoInput, riga: RigaVerifica) -> Passo:
    return Passo(
        simbolo="σ_min", formula="N / (A_X * B_Y) * (1 - 6 * abs(e_X) / A_X - 6 * abs(e_Y) / B_Y)",
        valori=(
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="A_X", valore=inputs.ax_m, unita="m"),
            Valore(simbolo="B_Y", valore=inputs.by_m, unita="m"),
            Valore(simbolo="e_X", valore=riga.ex_m, unita="m"),
            Valore(simbolo="e_Y", valore=riga.ey_m, unita="m"),
        ),
        risultato=riga.sigma_min_kpa, unita="kPa", clausola=NTC_PORTANZA_NAVIER,
    )


def _passo_verifica_portanza(inputs: PlintoIsolatoInput, riga: RigaVerifica) -> Passo:
    resistenza: ResistenzaRow = next(r for r in inputs.resistenze if r.famiglia == riga.famiglia)
    sigma_amm = sigma_ammissibile_kpa(resistenza.sigma_ammissibile, sistema_unita=inputs.sistema_unita, legacy_compat=False)
    soddisfatta = riga.sigma_max_kpa <= sigma_amm
    return Passo(
        simbolo="σ_max/σ_amm", formula="σ_max <= σ_amm",
        valori=(
            Valore(simbolo="σ_max", valore=riga.sigma_max_kpa, unita="kPa"),
            Valore(simbolo="σ_amm", valore=sigma_amm, unita="kPa",
                   descrizione=f"resistenza ammissibile del terreno, famiglia {riga.famiglia}"),
        ),
        risultato=riga.sigma_max_kpa, unita="kPa", clausola=BEARING_CLAUSE,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Verifica 'Portanza ({riga.famiglia})'.",
    )

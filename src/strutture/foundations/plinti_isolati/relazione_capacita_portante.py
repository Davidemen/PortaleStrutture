"""`relazione.py` (docs/architecture-phase2.md §6): NTC2018 §6.4.2.1 / EN 1997-1 Annesso D bearing
capacity, on the ROW that governs `output.capacita_portante.governante` (worst N_Ed/R_d, over
every ULS `famiglia`) — present only when the "Terreno" block is filled (`capacita_portante_riga.py`).
`Nq`/`Nc`/`Nγ`/shape/inclination factors are not exposed by `RigaCapacitaPortante` (only the final
`q_lim_kpa`/`r_d_kn`/`ratio` are), so this calls `verifica_drenata`/`verifica_non_drenata` — the
SAME `strutture.shared.capacita_portante` step functions `capacita_portante_riga.py` itself calls,
with the SAME arguments — to reach the full `VerificaCapacitaPortante` breakdown (docs §1 "may call
the package's own step functions for an intermediate the output does not expose").

Base-inclination factors (`b_q`/`b_γ`/`b_c`) are always 1.0 in this tool (no input exposes a
tilted base) but are read off `VerificaCapacitaPortante` rather than hardcoded; `sγ`/`iγ` are read
the same way rather than re-derived, to keep the `q_lim` Passo to one step (docs §5, 8-25 steps
per tool)."""
import math

from strutture.shared.capacita_portante import (
    AreaEfficace,
    CaricoLimiteResult,
    FattoriInclinazioneBase,
    FattoriInclinazioneCarico,
    FattoriPortanza,
    VerificaCapacitaPortante,
    verifica_drenata,
    verifica_non_drenata,
)
from strutture.shared.capacita_portante.verifica import GAMMA_R_STATICO_NTC_6_4_2_1
from strutture.shared.relazione import Passo, Traccia, Valore

from .capacita_portante import FAMIGLIE_SISMICHE
from .capacita_portante_checks import CLAUSOLA, CLAUSOLA_SISMICA
from .capacita_portante_riga import RigaCapacitaPortante
from .input import PlintoIsolatoInput
from .models import PlintoIsolatoOutput
from .relazione_helpers import trova_riga
from .riga_verifica import RigaVerifica

CLAUSOLA_ANNESSO_D4 = "EN 1997-1 Annesso D.4"
CLAUSOLA_ANNESSO_D2 = "EN 1997-1 Annesso D.2"
CLAUSOLA_ANNESSO_D1 = "EN 1997-1 Annesso D.1"
CLAUSOLA_ANNESSO_D3 = "EN 1997-1 Annesso D.3"


def traccia_capacita_portante(inputs: PlintoIsolatoInput, output: PlintoIsolatoOutput) -> Traccia | None:
    """`None` when the "Terreno" block is empty or produced no governing row (no ULS `famiglia` in
    `reazioni`)."""
    governante = output.capacita_portante.governante
    if inputs.terreno_condizione is None or governante is None:
        return None
    riga = trova_riga(output.righe, governante.nodo, governante.combo)
    verifica = _verifica(inputs, riga)
    passi_fattori = (_passi_drenata(inputs, riga, verifica) if inputs.terreno_condizione == "drenata"
                      else _passi_non_drenata(inputs, riga, verifica))
    passi = (*passi_fattori, _passo_r_d(verifica), _passo_ratio(governante))
    titolo = f"Capacità portante (Annesso D) — combinazione governante {governante.combo} ({governante.famiglia})"
    return Traccia(titolo=titolo, passi=passi)


def _verifica(inputs: PlintoIsolatoInput, riga: RigaVerifica) -> VerificaCapacitaPortante:
    """Same call `capacita_portante_riga.py` makes for `riga`, kept here only to reach the
    intermediate factor breakdown it does not return."""
    h_kn = math.hypot(riga.vx_kN, riga.vy_kN)
    theta_deg = math.degrees(math.atan2(riga.vx_kN, riga.vy_kN)) if h_kn > 0 else 0.0
    profondita_m = inputs.h_interro_m + inputs.h_plinto_m
    if inputs.terreno_condizione == "drenata":
        return verifica_drenata(
            n_ed_kn=riga.n_kN, b_m=inputs.ax_m, l_m=inputs.by_m, eb_m=riga.ex_m, el_m=riga.ey_m,
            phi_k_deg=inputs.terreno_phi_k_deg, c_k_kpa=inputs.terreno_c_k_kpa,
            gamma_kn_m3=inputs.terreno_gamma_kn_m3, profondita_piano_posa_m=profondita_m,
            profondita_falda_m=inputs.terreno_profondita_falda_m, h_kn=h_kn, direzione_h="theta", theta_deg=theta_deg,
        )
    return verifica_non_drenata(
        n_ed_kn=riga.n_kN, b_m=inputs.ax_m, l_m=inputs.by_m, eb_m=riga.ex_m, el_m=riga.ey_m,
        cu_k_kpa=inputs.terreno_cu_k_kpa, gamma_kn_m3=inputs.terreno_gamma_kn_m3,
        profondita_piano_posa_m=profondita_m, h_kn=h_kn,
    )


def _passi_drenata(inputs: PlintoIsolatoInput, riga: RigaVerifica, verifica: VerificaCapacitaPortante) -> tuple[Passo, ...]:
    cl = verifica.carico_limite
    portanza, forma, base, incl = cl.fattori_portanza, cl.fattori_forma, cl.fattori_inclinazione_base, cl.fattori_inclinazione_carico
    if portanza is None:
        raise ValueError("carico_limite_drenato non ha valorizzato fattori_portanza (Nq/Nc/Nγ)")
    nq_passo = _passo_nq(inputs, portanza.nq)
    nc_passo = _passo_nc(inputs, portanza.nq, portanza.nc)
    ngamma_passo = _passo_ngamma(inputs, portanza.nq, portanza.ngamma)
    sq_passo = _passo_sq(inputs, cl.area_efficace, forma.sq)
    sc_passo = _passo_sc(sq_passo, nq_passo, forma.sc)
    iq_passo = _passo_iq(inputs, riga, cl.area_efficace, incl, verifica.n_ed_kn)
    ic_passo = _passo_ic(iq_passo, nc_passo, inputs.terreno_phi_k_deg, incl.ic)
    qlim_passo = _passo_q_lim_drenata(inputs, cl, base, portanza, nq_passo, nc_passo, sq_passo, sc_passo, iq_passo, ic_passo)
    return nq_passo, nc_passo, ngamma_passo, sq_passo, sc_passo, iq_passo, ic_passo, qlim_passo


def _passo_nq(inputs: PlintoIsolatoInput, nq: float) -> Passo:
    psi_deg = 45.0 + inputs.terreno_phi_k_deg / 2.0
    return Passo(
        simbolo="N_q", formula="exp(π * tan(φ'_k)) * tan(ψ)^2",
        valori=(
            Valore(simbolo="π", valore=math.pi),
            Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°", descrizione="angolo di attrito caratteristico"),
            Valore(simbolo="ψ", valore=psi_deg, unita="°", descrizione="45° + φ'_k/2"),
        ),
        risultato=nq, unita="-", clausola=CLAUSOLA_ANNESSO_D4,
    )


def _passo_nc(inputs: PlintoIsolatoInput, nq: float, nc: float) -> Passo:
    return Passo(
        simbolo="N_c", formula="(N_q - 1) / tan(φ'_k)",
        valori=(Valore(simbolo="N_q", valore=nq), Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°")),
        risultato=nc, unita="-", clausola=CLAUSOLA_ANNESSO_D4,
    )


def _passo_ngamma(inputs: PlintoIsolatoInput, nq: float, ngamma: float) -> Passo:
    return Passo(
        simbolo="N_γ", formula="2 * (N_q - 1) * tan(φ'_k)",
        valori=(Valore(simbolo="N_q", valore=nq), Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°")),
        risultato=ngamma, unita="-", clausola=CLAUSOLA_ANNESSO_D4,
        nota="Fattore di capacità portante per base scabra (EN 1997-1 Annesso D.4).",
    )


def _passo_sq(inputs: PlintoIsolatoInput, area: AreaEfficace, sq: float) -> Passo:
    return Passo(
        simbolo="s_q", formula="1 + (B' / L') * sin(φ'_k)",
        valori=(
            Valore(simbolo="B'", valore=area.b_eff_m, unita="m", descrizione="larghezza efficace (Meyerhof)"),
            Valore(simbolo="L'", valore=area.l_eff_m, unita="m", descrizione="lunghezza efficace (Meyerhof)"),
            Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°"),
        ),
        risultato=sq, unita="-", clausola=CLAUSOLA_ANNESSO_D2,
    )


def _passo_sc(sq_passo: Passo, nq_passo: Passo, sc: float) -> Passo:
    return Passo(
        simbolo="s_c", formula="(s_q * N_q - 1) / (N_q - 1)",
        valori=(Valore(simbolo="s_q", valore=sq_passo.risultato), Valore(simbolo="N_q", valore=nq_passo.risultato)),
        risultato=sc, unita="-", clausola=CLAUSOLA_ANNESSO_D2,
    )


def _passo_iq(
    inputs: PlintoIsolatoInput, riga: RigaVerifica, area: AreaEfficace, incl: FattoriInclinazioneCarico, n_ed_kn: float,
) -> Passo:
    h_kn = math.hypot(riga.vx_kN, riga.vy_kN)
    return Passo(
        simbolo="i_q", formula="(1 - H / (N_Ed + A' * c'_k / tan(φ'_k)))^m",
        valori=(
            Valore(simbolo="H", valore=h_kn, unita="kN", descrizione="risultante orizzontale alla base, H = √(Vx²+Vy²)"),
            Valore(simbolo="N_Ed", valore=n_ed_kn, unita="kN"),
            Valore(simbolo="A'", valore=area.a_eff_m2, unita="m2", descrizione="area efficace B'×L'"),
            Valore(simbolo="c'_k", valore=inputs.terreno_c_k_kpa, unita="kPa"),
            Valore(simbolo="φ'_k", valore=inputs.terreno_phi_k_deg, unita="°"),
            Valore(simbolo="m", valore=incl.m, descrizione="esponente EN 1997-1 Annesso D.2, da B'/L' e dalla direzione di H"),
        ),
        risultato=incl.iq, unita="-", clausola=CLAUSOLA_ANNESSO_D2,
    )


def _passo_ic(iq_passo: Passo, nc_passo: Passo, phi_k_deg: float, ic: float) -> Passo:
    return Passo(
        simbolo="i_c", formula="max(i_q - (1 - i_q) / (N_c * tan(φ'_k)), 0)",
        valori=(
            Valore(simbolo="i_q", valore=iq_passo.risultato),
            Valore(simbolo="N_c", valore=nc_passo.risultato),
            Valore(simbolo="φ'_k", valore=phi_k_deg, unita="°"),
        ),
        risultato=ic, unita="-", clausola=CLAUSOLA_ANNESSO_D2,
    )


def _passo_q_lim_drenata(
    inputs: PlintoIsolatoInput, cl: CaricoLimiteResult, base: FattoriInclinazioneBase, portanza: FattoriPortanza,
    nq_passo: Passo, nc_passo: Passo, sq_passo: Passo, sc_passo: Passo, iq_passo: Passo, ic_passo: Passo,
) -> Passo:
    formula = "c'_k*N_c*b_c*s_c*i_c + q'*N_q*b_q*s_q*i_q + 0.5*γ'*B'*N_γ*b_γ*s_γ*i_γ"
    valori = (
        Valore(simbolo="c'_k", valore=inputs.terreno_c_k_kpa, unita="kPa", descrizione="coesione efficace caratteristica"),
        Valore(simbolo="N_c", valore=nc_passo.risultato),
        Valore(simbolo="b_c", valore=base.bc, descrizione="fattore di inclinazione della base (base orizzontale, α=0)"),
        Valore(simbolo="s_c", valore=sc_passo.risultato),
        Valore(simbolo="i_c", valore=ic_passo.risultato),
        Valore(simbolo="q'", valore=cl.q_eff_kpa, unita="kPa", descrizione="sovraccarico efficace al piano di posa"),
        Valore(simbolo="N_q", valore=nq_passo.risultato),
        Valore(simbolo="b_q", valore=base.bq, descrizione="fattore di inclinazione della base (base orizzontale, α=0)"),
        Valore(simbolo="s_q", valore=sq_passo.risultato),
        Valore(simbolo="i_q", valore=iq_passo.risultato),
        Valore(simbolo="γ'", valore=cl.gamma_eff_kn_m3, unita="kN/m3", descrizione="peso di volume efficace nel termine di N_γ"),
        Valore(simbolo="B'", valore=cl.area_efficace.b_eff_m, unita="m"),
        Valore(simbolo="N_γ", valore=portanza.ngamma),
        Valore(simbolo="b_γ", valore=base.bgamma, descrizione="fattore di inclinazione della base (base orizzontale, α=0)"),
        Valore(simbolo="s_γ", valore=cl.fattori_forma.sgamma),
        Valore(simbolo="i_γ", valore=cl.fattori_inclinazione_carico.igamma),
    )
    return Passo(
        simbolo="q_lim", formula=formula, valori=valori, risultato=cl.q_lim_kpa, unita="kPa", clausola=CLAUSOLA_ANNESSO_D1,
        nota="Pressione limite di capacità portante, condizione drenata.",
    )


def _passi_non_drenata(inputs: PlintoIsolatoInput, riga: RigaVerifica, verifica: VerificaCapacitaPortante) -> tuple[Passo, ...]:
    cl = verifica.carico_limite
    area = cl.area_efficace
    h_kn = math.hypot(riga.vx_kN, riga.vy_kN)
    sc_passo = Passo(
        simbolo="s_c", formula="1 + 0.2 * (B' / L')",
        valori=(Valore(simbolo="B'", valore=area.b_eff_m, unita="m"), Valore(simbolo="L'", valore=area.l_eff_m, unita="m")),
        risultato=cl.fattori_forma.sc, unita="-", clausola=CLAUSOLA_ANNESSO_D3,
    )
    ic_passo = Passo(
        simbolo="i_c", formula="0.5 * (1 + sqrt(1 - H / (A' * c_u,k)))",
        valori=(
            Valore(simbolo="H", valore=h_kn, unita="kN", descrizione="risultante orizzontale alla base"),
            Valore(simbolo="A'", valore=area.a_eff_m2, unita="m2", descrizione="area efficace B'×L'"),
            Valore(simbolo="c_u,k", valore=inputs.terreno_cu_k_kpa, unita="kPa"),
        ),
        risultato=cl.fattori_inclinazione_carico.ic, unita="-", clausola=CLAUSOLA_ANNESSO_D3,
    )
    qlim_passo = Passo(
        simbolo="q_lim", formula="(π + 2) * c_u,k * b_c * s_c * i_c + q",
        valori=(
            Valore(simbolo="π", valore=math.pi),
            Valore(simbolo="c_u,k", valore=inputs.terreno_cu_k_kpa, unita="kPa"),
            Valore(simbolo="b_c", valore=cl.fattori_inclinazione_base.bc, descrizione="fattore di inclinazione della base (base orizzontale, α=0)"),
            Valore(simbolo="s_c", valore=sc_passo.risultato),
            Valore(simbolo="i_c", valore=ic_passo.risultato),
            Valore(simbolo="q", valore=cl.q_eff_kpa, unita="kPa", descrizione="sovraccarico totale al piano di posa"),
        ),
        risultato=cl.q_lim_kpa, unita="kPa", clausola=CLAUSOLA_ANNESSO_D3,
        nota="Pressione limite di capacità portante, condizione non drenata.",
    )
    return sc_passo, ic_passo, qlim_passo


def _passo_r_d(verifica: VerificaCapacitaPortante) -> Passo:
    area = verifica.carico_limite.area_efficace
    return Passo(
        simbolo="R_d", formula=f"q_lim * A' / {GAMMA_R_STATICO_NTC_6_4_2_1:g}",
        valori=(
            Valore(simbolo="q_lim", valore=verifica.carico_limite.q_lim_kpa, unita="kPa"),
            Valore(simbolo="A'", valore=area.a_eff_m2, unita="m2", descrizione="area efficace B'×L'"),
        ),
        risultato=verifica.r_d_kn, unita="kN", clausola=CLAUSOLA,
        nota=f"γR = {GAMMA_R_STATICO_NTC_6_4_2_1:g}, {CLAUSOLA} (approccio 2, A1+M1+R3).",
    )


def _passo_ratio(governante: RigaCapacitaPortante) -> Passo:
    sismica = governante.famiglia in FAMIGLIE_SISMICHE
    return Passo(
        simbolo="N_Ed/R_d", formula="N_Ed/R_d <= 1",
        valori=(Valore(simbolo="N_Ed", valore=governante.n_ed_kn, unita="kN"), Valore(simbolo="R_d", valore=governante.r_d_kn, unita="kN")),
        risultato=governante.ratio, unita="-", clausola=CLAUSOLA_SISMICA if sismica else CLAUSOLA,
        esito="soddisfatta" if governante.ratio <= 1.0 else "non soddisfatta",
        nota=("Famiglia sismica: formula statica dell'Annesso D, riduzione inerziale del terreno "
              "(Paolucci-Pecker) non applicata — esito da confermare con il progettista." if sismica else ""),
    )

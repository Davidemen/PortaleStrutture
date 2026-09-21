"""Tool registration: `muro-sostegno` (cantilever retaining wall, per metre run).

One composed Tool per docs/BUILD_CONTRACT.md "Member tools": `run_muro_sostegno` composes the
small step modules (geometria, parametri_sismici, angoli_progetto, coulomb/mononobe_okabe,
ribaltamento_scorrimento, pressioni_terreno, armatura_paramento, armatura_fondazione_valle,
armatura_fondazione_monte) for all 8 combinations (STR_1, STR_2, GEO_1, GEO_2, EQU_1, EQU_2,
SISMA_1, SISMA_2) and returns every intermediate group.
"""
import logging
import math

from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.ntc_combos import fattori_resistenza
from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tool import Tool

from . import armatura_fondazione_monte as fond_monte
from . import armatura_fondazione_valle as fond_valle
from . import armatura_paramento as paramento
from . import rebar_selection
from .angoli_progetto import delta_d_rad, phi_d_rad
from .combinazioni import ALL_COMBOS, SEISMIC_COMBOS, fattori_combo
from .coulomb import ka_coulomb
from .geometria import geometria_muro
from .models import (
    ArmaturaFondazioneMonteCombo,
    ArmaturaFondazioneMonteResult,
    ArmaturaFondazioneValleCombo,
    ArmaturaFondazioneValleResult,
    ArmaturaParamentoCombo,
    ArmaturaParamentoResult,
    GeometriaResult,
    MuroSostegnoInput,
    MuroSostegnoOutput,
    NomeCombo,
    PressioniCombo,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)
from .mononobe_okabe import coefficienti_sismici, kae_mononobe_okabe
from .parametri_sismici import parametri_sismici
from .pesi import pesi_combo
from .pressioni_terreno import eccentricita_risultante, eccentricita_termine, larghezza_efficace, pressioni_valle_monte
from .ribaltamento_scorrimento import (
    GAMMA_R_RIBALTAMENTO_R3,
    fattore_sicurezza_ribaltamento,
    fattore_sicurezza_scorrimento,
    momento_ribaltante,
    momento_stabilizzante,
    risultante_orizzontale,
    risultante_verticale,
    soglia_verifica,
    spinte_orizzontali_verticali,
)
from .schizzo import disegna as disegna_schizzo

logger = logging.getLogger(__name__)

# docs/specs/muro-sostegno.md §"Golden test case" (Tratto A, cached against the original sheet).
ESEMPIO_TRATTO_A = {
    "gamma_terr_sat_kN_m3": 19.7, "gamma_terr_secco_kN_m3": 15.6, "phi_deg": 30.69, "delta_deg": 0,
    "beta_deg": 0, "psi_deg": 90, "omega_deg": 0, "ag_g": 0.136, "f0": 2.419,
    "categoria_sottosuolo": "C", "categoria_topografica": "T1", "beta_m": 0.24, "gamma_e": 1.0,
    "gamma_cls_kN_m3": 25, "s_base_m": 0.49, "s_top_m": 0.25, "s_fond_m": 0.3, "h_muro_m": 2.4,
    "b_valle_m": 0.26, "b_monte_m": 1.15, "q_kN_m2": 2, "copertura_paramento_m": 0.06,
    "grado_acciaio": "B450C", "passo_arm_paramento_m": 0.2, "copertura_fondazione_m": 0.06,
    "passo_arm_fondazione_m": 0.2,
}

CLAUSE_RIBALTAMENTO = "NTC2018 §6.5.3.1.2"
CLAUSE_SCORRIMENTO = "NTC2018 §6.5.3.1.1 / EC7 §6.5.4"
AVVISO_CAPACITA_PORTANTE = (
    "La verifica a collasso per capacità portante del terreno (NTC2018 §6.5.3.1.1, γR=1.4 statico / "
    "1.2 sismico, Tab. 6.5.I) non è calcolata da questo strumento: usare uno strumento geotecnico "
    "dedicato per confrontare la pressione di contatto con qlim. L'eccentricità è qui verificata solo "
    "contro |e| > B/2 (risultante fuori dalla fondazione), non contro i limiti di normativa dell'§6.4.2.1."
)


def _spinta_combo(nome: NomeCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, s_sismico: float) -> SpintaCombo:
    fattori = fattori_combo(nome, legacy_compat=inputs.legacy_compat)
    phi_d = phi_d_rad(inputs.phi_deg, fattori.gamma_phi_terr, legacy_compat=inputs.legacy_compat)
    delta_d = delta_d_rad(inputs.delta_deg, fattori.gamma_phi_terr, legacy_compat=inputs.legacy_compat)
    beta_rad, psi_rad = math.radians(inputs.beta_deg), math.radians(inputs.psi_deg)
    sismica = nome in SEISMIC_COMBOS
    kh = kv = theta_rad = None
    kv_factor = 1.0
    if sismica:
        segno_kv = 1.0 if nome == "SISMA_1" else -1.0
        kh, kv, theta_rad = coefficienti_sismici(s=s_sismico, ag_g=inputs.ag_g, beta_m=inputs.beta_m, segno_kv=segno_kv)
        if not inputs.legacy_compat:
            # EN1998-5 §7.3.2.2(2)P / NTC2018 §7.11.6.2.1: the same vertical seismic coefficient kv
            # that de-rates/up-rates the thrust also scales the monolith's own stabilising weight.
            kv_factor = 1 + kv
        ka = kae_mononobe_okabe(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta_rad, psi_rad=psi_rad, theta_rad=theta_rad)
    else:
        ka = ka_coulomb(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta_rad, psi_rad=psi_rad)
    pesi = pesi_combo(
        gamma_cls_kN_m3=inputs.gamma_cls_kN_m3,
        gamma_terr_sat_kN_m3=inputs.gamma_terr_sat_kN_m3,
        geometria=geometria,
        gamma_g_muro=fattori.gamma_g_muro,
        gamma_g_terr=fattori.gamma_g_terr,
        kv_factor=kv_factor,
    )
    return SpintaCombo(
        nome=nome,
        sismica=sismica,
        gamma_g_muro=fattori.gamma_g_muro,
        gamma_phi_terr=fattori.gamma_phi_terr,
        gamma_g_terr=fattori.gamma_g_terr,
        gamma_q=fattori.gamma_q,
        phi_d_rad=phi_d,
        delta_d_rad=delta_d,
        w_muro_kN=pesi.w_muro_kN,
        m_muro_kNm=pesi.m_muro_kNm,
        w_terr_kN=pesi.w_terr_kN,
        m_terr_kNm=pesi.m_terr_kNm,
        ka=ka,
        kh=kh,
        kv=kv,
        theta_rad=theta_rad,
    )


def _ribaltamento_scorrimento_combo(spinta: SpintaCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult) -> RibaltamentoScorrimentoCombo:
    dq_kN_m2 = inputs.q_kN_m2 * spinta.gamma_q
    fattore_sismico = (1 + spinta.kv) * inputs.gamma_e if spinta.sismica else 1.0
    braccio_terr_m = geometria.h_muro_tot_m / 2 if spinta.sismica else geometria.h_muro_tot_m / 3
    forze = spinte_orizzontali_verticali(
        ka=spinta.ka,
        delta_d_rad=spinta.delta_d_rad,
        dq_kN_m2=dq_kN_m2,
        h_tot_m=geometria.h_muro_tot_m,
        gamma_g_terr=spinta.gamma_g_terr,
        gamma_terr_kN_m3=inputs.gamma_terr_sat_kN_m3,
        fattore_sismico=fattore_sismico,
    )
    # EN1998-5 §7.3.2.2(2)P / NTC2018 §7.11.6.2.1: horizontal inertia force of the wall+backfill
    # monolith (kh already scales the seismic thrust via Mononobe-Okabe; it must also scale the
    # monolith's own mass, on top of MSTAB/Ntot already carrying the (1±kv) weight from `pesi_combo`).
    fh_kN = 0.0
    m_fh_kNm = 0.0
    if spinta.sismica and not inputs.legacy_compat:
        fh_kN = spinta.kh * (spinta.w_muro_kN + spinta.w_terr_kN)
        m_fh_kNm = spinta.kh * (spinta.w_muro_kN * geometria.z_muro_m + spinta.w_terr_kN * geometria.z_terr_m)
    m_rib_kNm = momento_ribaltante(
        sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN, h_tot_m=geometria.h_muro_tot_m, braccio_terr_m=braccio_terr_m, m_fh_kNm=m_fh_kNm
    )
    m_stab_kNm = momento_stabilizzante(
        sv_q_kN=forze.sv_q_kN, sv_terr_kN=forze.sv_terr_kN, x_sv_m=geometria.x_sv_m, m_terr_kNm=spinta.m_terr_kNm, m_muro_kNm=spinta.m_muro_kNm
    )
    n_tot_kN = risultante_verticale(w_muro_kN=spinta.w_muro_kN, w_terr_kN=spinta.w_terr_kN, sv_q_kN=forze.sv_q_kN, sv_terr_kN=forze.sv_terr_kN)
    r_tot_kN = risultante_orizzontale(sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN, fh_kN=fh_kN)
    or_ribaltamento = fattore_sicurezza_ribaltamento(m_stab_kNm=m_stab_kNm, m_rib_kNm=m_rib_kNm)
    os_scorrimento = fattore_sicurezza_scorrimento(
        phi_d_rad=spinta.phi_d_rad, n_tot_kN=n_tot_kN, r_tot_kN=r_tot_kN, omega_rad=math.radians(inputs.omega_deg)
    )
    # NTC2018 Tab. 6.5.I γR (Approccio 2, A1+M1+R3 per le opere di sostegno, §6.5.3.1.1): the sheet
    # (`legacy_compat=True`) never divides the resistance by γR, i.e. it checks OR/OS >= 1.
    soglia_rib = soglia_verifica(sismica=spinta.sismica, legacy_compat=inputs.legacy_compat, gamma_r_statico=GAMMA_R_RIBALTAMENTO_R3)
    soglia_scorr = soglia_verifica(sismica=spinta.sismica, legacy_compat=inputs.legacy_compat, gamma_r_statico=fattori_resistenza("scorrimento").r3)
    return RibaltamentoScorrimentoCombo(
        nome=spinta.nome,
        dq_kN_m2=dq_kN_m2,
        sh_q_kN=forze.sh_q_kN,
        sh_terr_kN=forze.sh_terr_kN,
        sv_q_kN=forze.sv_q_kN,
        sv_terr_kN=forze.sv_terr_kN,
        braccio_terr_m=braccio_terr_m,
        fh_kN=fh_kN,
        m_fh_kNm=m_fh_kNm,
        m_rib_kNm=m_rib_kNm,
        m_stab_kNm=m_stab_kNm,
        n_tot_kN=n_tot_kN,
        r_tot_kN=r_tot_kN,
        or_ribaltamento=or_ribaltamento,
        os_scorrimento=os_scorrimento,
        verifica_ribaltamento=Check(
            name=f"Ribaltamento {_nome_combo_leggibile(spinta.nome)}",
            passed=or_ribaltamento >= soglia_rib,
            detail=f"OR={or_ribaltamento:.3f} (soglia γR={soglia_rib:.2f})",
            clause=CLAUSE_RIBALTAMENTO,
            value=or_ribaltamento,
            limit=soglia_rib,
            unit="-",
        ),
        verifica_scorrimento=Check(
            name=f"Scorrimento {_nome_combo_leggibile(spinta.nome)}",
            passed=os_scorrimento >= soglia_scorr,
            detail=f"OS={os_scorrimento:.3f} (soglia γR={soglia_scorr:.2f})",
            clause=CLAUSE_SCORRIMENTO,
            value=os_scorrimento,
            limit=soglia_scorr,
            unit="-",
        ),
    )


def _nome_combo_leggibile(nome: NomeCombo) -> str:
    """Nome del check, leggibile anche se l'interfaccia tronca il testo: le combinazioni sismiche
    SISMA_1/SISMA_2 differiscono solo nell'ultimo carattere (il segno di kv), che un'interfaccia che
    tronca a larghezza fissa può nascondere — il segno è quindi richiamato esplicitamente."""
    if nome == "SISMA_1":
        return f"{nome} (+kv)"
    if nome == "SISMA_2":
        return f"{nome} (−kv)"
    return nome


def _pressioni_combo(spinta: SpintaCombo, verifica: RibaltamentoScorrimentoCombo, *, geometria: GeometriaResult) -> PressioniCombo:
    e_muro_m, m_muro_ecc_kNm = eccentricita_termine(spinta.w_muro_kN, geometria.x_muro_m, geometria.b_fond_m)
    e_terr_m, m_terr_ecc_kNm = eccentricita_termine(spinta.w_terr_kN, geometria.x_terr_m, geometria.b_fond_m)
    sv_tot_kN = verifica.sv_q_kN + verifica.sv_terr_kN
    e_sv_m, m_sv_ecc_kNm = eccentricita_termine(sv_tot_kN, geometria.x_sv_m, geometria.b_fond_m)
    m_tot_kNm, eccentricita_m = eccentricita_risultante(
        m_rib_kNm=verifica.m_rib_kNm, m_muro_ecc_kNm=m_muro_ecc_kNm, m_terr_ecc_kNm=m_terr_ecc_kNm, m_sv_ecc_kNm=m_sv_ecc_kNm, n_tot_kN=verifica.n_tot_kN
    )
    if abs(eccentricita_m) > geometria.b_fond_m / 2:
        raise CalcError(
            f"Combinazione {spinta.nome}: eccentricità |e|={abs(eccentricita_m):.3f} m supera B/2={geometria.b_fond_m / 2:.3f} m "
            "(risultante esterna alla fondazione, verifica di pressione sul terreno non significativa)"
        )
    b_star_m = larghezza_efficace(eccentricita_m=eccentricita_m, b_fond_m=geometria.b_fond_m)
    pressioni = pressioni_valle_monte(n_tot_kN=verifica.n_tot_kN, m_tot_kNm=m_tot_kNm, b_fond_m=geometria.b_fond_m, b_star_m=b_star_m)
    return PressioniCombo(
        nome=spinta.nome,
        e_muro_m=e_muro_m,
        e_terr_m=e_terr_m,
        e_sv_m=e_sv_m,
        m_tot_kNm=m_tot_kNm,
        n_tot_kN=verifica.n_tot_kN,
        eccentricita_m=eccentricita_m,
        entro_nocciolo=b_star_m == 0,
        b_star_m=b_star_m,
        p_valle_kPa=pressioni.p_valle_kPa,
        p_monte_kPa=pressioni.p_monte_kPa,
    )


def _armatura_paramento_combo(
    spinta: SpintaCombo, verifica: RibaltamentoScorrimentoCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaParamentoCombo:
    if inputs.legacy_compat:
        zq_m = paramento.leva_sovraccarico_m(h_muro_tot_m=geometria.h_muro_tot_m, s_fond_m=inputs.s_fond_m)
        zterr_m = paramento.leva_terreno_m(braccio_terr_m=verifica.braccio_terr_m, s_fond_m=inputs.s_fond_m)
        m_ed_kNm = paramento.momento_flettente_kNm(sh_q_kN=verifica.sh_q_kN, sh_terr_kN=verifica.sh_terr_kN, zq_m=zq_m, zterr_m=zterr_m)
    else:
        # Fixed behaviour (NTC2018 §6.5.3.1.1/§4.1.2): the stem's own thrust over its own height
        # hs = H - sfond, not Tool 2's full-height resultants reused with shifted lever arms.
        hs_m = geometria.h_muro_tot_m - inputs.s_fond_m
        fattore_sismico = (1 + spinta.kv) * inputs.gamma_e if spinta.sismica else 1.0
        forze_stelo = paramento.spinte_stelo(
            ka=spinta.ka,
            delta_d_rad=spinta.delta_d_rad,
            dq_kN_m2=verifica.dq_kN_m2,
            hs_m=hs_m,
            gamma_g_terr=spinta.gamma_g_terr,
            gamma_terr_kN_m3=inputs.gamma_terr_sat_kN_m3,
            fattore_sismico=fattore_sismico,
        )
        zq_m = paramento.leva_sovraccarico_stelo_m(hs_m=hs_m)
        zterr_m = paramento.leva_terreno_stelo_m(hs_m=hs_m)
        m_ed_kNm = paramento.momento_flettente_kNm(sh_q_kN=forze_stelo.sh_q_kN, sh_terr_kN=forze_stelo.sh_terr_kN, zq_m=zq_m, zterr_m=zterr_m)
    d_m = inputs.s_base_m - inputs.copertura_paramento_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaParamentoCombo(nome=spinta.nome, zq_m=zq_m, zterr_m=zterr_m, m_ed_kNm=m_ed_kNm, as_nec_cm2_m=as_nec_cm2_m)


def _armatura_fondazione_valle_combo(
    spinta: SpintaCombo, pressioni: PressioniCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaFondazioneValleCombo:
    p_star_kPa = fond_valle.pressione_interpolata_kPa(
        b_star_m=pressioni.b_star_m, p_valle_kPa=pressioni.p_valle_kPa, p_monte_kPa=pressioni.p_monte_kPa, b_fond_m=geometria.b_fond_m, x_star_m=inputs.b_valle_m
    )
    m_ed_p1_kNm = fond_valle.momento_pressione_1_kNm(p_star_kPa=p_star_kPa, p_valle_kPa=pressioni.p_valle_kPa, b_valle_m=inputs.b_valle_m)
    m_ed_p2_kNm = fond_valle.momento_pressione_2_kNm(
        p_star_kPa=p_star_kPa, p_valle_kPa=pressioni.p_valle_kPa, b_star_m=pressioni.b_star_m, b_valle_m=inputs.b_valle_m
    )
    m_ed_fond_kNm = fond_valle.momento_autopeso_kNm(
        gamma_g_muro=spinta.gamma_g_muro, s_fond_m=inputs.s_fond_m, gamma_cls_kN_m3=inputs.gamma_cls_kN_m3, b_valle_m=inputs.b_valle_m
    )
    m_ed_tot_kNm = m_ed_p1_kNm + m_ed_p2_kNm + m_ed_fond_kNm
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_tot_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaFondazioneValleCombo(
        nome=spinta.nome,
        p_star_kPa=p_star_kPa,
        m_ed_p1_kNm=m_ed_p1_kNm,
        m_ed_p2_kNm=m_ed_p2_kNm,
        m_ed_fond_kNm=m_ed_fond_kNm,
        m_ed_tot_kNm=m_ed_tot_kNm,
        as_nec_cm2_m=as_nec_cm2_m,
    )


def _armatura_fondazione_monte_combo(
    spinta: SpintaCombo,
    verifica: RibaltamentoScorrimentoCombo,
    pressioni: PressioniCombo,
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
    fyd_MPa: float,
) -> ArmaturaFondazioneMonteCombo:
    p_star_star_kPa = fond_monte.pressione_interpolata_kPa(
        b_star_m=pressioni.b_star_m, p_valle_kPa=pressioni.p_valle_kPa, p_monte_kPa=pressioni.p_monte_kPa, b_fond_m=geometria.b_fond_m, b_monte_m=inputs.b_monte_m
    )
    m_ed_p_kNm = fond_monte.momento_pressione_kNm(
        p_monte_kPa=pressioni.p_monte_kPa, p_star_star_kPa=p_star_star_kPa, b_monte_m=inputs.b_monte_m, b_fond_m=geometria.b_fond_m, b_star_m=pressioni.b_star_m
    )
    m_ed_terr_kNm = fond_monte.momento_terreno_kNm(w_terr_kN=spinta.w_terr_kN, b_monte_m=inputs.b_monte_m, b_fond_m=geometria.b_fond_m, x_terr_m=geometria.x_terr_m)
    sv_tot_kN = verifica.sv_q_kN + verifica.sv_terr_kN
    m_ed_sv_kNm = fond_monte.momento_sovraccarico_verticale_kNm(
        sv_tot_kN=sv_tot_kN, x_sv_m=geometria.x_sv_m, b_fond_m=geometria.b_fond_m, b_monte_m=inputs.b_monte_m
    )
    m_ed_fond_kNm = fond_monte.momento_autopeso_kNm(
        b_monte_m=inputs.b_monte_m, gamma_g_muro=spinta.gamma_g_muro, gamma_cls_kN_m3=inputs.gamma_cls_kN_m3, s_fond_m=inputs.s_fond_m
    )
    m_ed_tot_kNm = m_ed_terr_kNm + m_ed_sv_kNm + m_ed_fond_kNm + m_ed_p_kNm
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_tot_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaFondazioneMonteCombo(
        nome=spinta.nome,
        p_star_star_kPa=p_star_star_kPa,
        m_ed_p_kNm=m_ed_p_kNm,
        m_ed_terr_kNm=m_ed_terr_kNm,
        m_ed_sv_kNm=m_ed_sv_kNm,
        m_ed_fond_kNm=m_ed_fond_kNm,
        m_ed_tot_kNm=m_ed_tot_kNm,
        as_nec_cm2_m=as_nec_cm2_m,
    )


def _run_armatura_paramento(
    spinte: tuple[SpintaCombo, ...], ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaParamentoResult:
    combinazioni = tuple(
        _armatura_paramento_combo(spinta, verifica, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    passo_m = inputs.passo_arm_paramento_m
    return ArmaturaParamentoResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )


def _run_armatura_fondazione_valle(
    spinte: tuple[SpintaCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...], *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaFondazioneValleResult:
    combinazioni = tuple(
        _armatura_fondazione_valle_combo(spinta, pressioni, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, pressioni in zip(spinte, pressioni_terreno, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    passo_m = inputs.passo_arm_fondazione_m
    return ArmaturaFondazioneValleResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )


def _run_armatura_fondazione_monte(
    spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...],
    pressioni_terreno: tuple[PressioniCombo, ...],
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
    fyd_MPa: float,
) -> ArmaturaFondazioneMonteResult:
    combinazioni = tuple(
        _armatura_fondazione_monte_combo(spinta, verifica, pressioni, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, verifica, pressioni in zip(spinte, ribaltamento_scorrimento, pressioni_terreno, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    passo_m = inputs.passo_arm_fondazione_m
    return ArmaturaFondazioneMonteResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_nec_governante_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )


def run_muro_sostegno(inputs: MuroSostegnoInput) -> Report[MuroSostegnoOutput]:
    geometria = geometria_muro(
        h_muro_m=inputs.h_muro_m, s_fond_m=inputs.s_fond_m, s_base_m=inputs.s_base_m, s_top_m=inputs.s_top_m, b_valle_m=inputs.b_valle_m, b_monte_m=inputs.b_monte_m
    )
    sismici = parametri_sismici(inputs.categoria_sottosuolo, inputs.categoria_topografica, inputs.f0, inputs.ag_g)

    spinte = tuple(_spinta_combo(nome, inputs=inputs, geometria=geometria, s_sismico=sismici.s) for nome in ALL_COMBOS)
    ribaltamento_scorrimento = tuple(_ribaltamento_scorrimento_combo(spinta, inputs=inputs, geometria=geometria) for spinta in spinte)
    pressioni_terreno = tuple(
        _pressioni_combo(spinta, verifica, geometria=geometria) for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True)
    )

    fyd_MPa = rebar_properties(inputs.grado_acciaio).fyd_MPa
    armatura_paramento = _run_armatura_paramento(spinte, ribaltamento_scorrimento, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
    armatura_fondazione_valle = _run_armatura_fondazione_valle(spinte, pressioni_terreno, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
    armatura_fondazione_monte = _run_armatura_fondazione_monte(
        spinte, ribaltamento_scorrimento, pressioni_terreno, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa
    )

    schizzo: Sketch | None
    try:
        schizzo = disegna_schizzo(inputs, geometria, spinte, ribaltamento_scorrimento, pressioni_terreno)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per muro-sostegno")
        schizzo = None

    data = MuroSostegnoOutput(
        geometria=geometria,
        parametri_sismici=sismici,
        spinte=spinte,
        ribaltamento_scorrimento=ribaltamento_scorrimento,
        pressioni_terreno=pressioni_terreno,
        armatura_paramento=armatura_paramento,
        armatura_fondazione_valle=armatura_fondazione_valle,
        armatura_fondazione_monte=armatura_fondazione_monte,
        schizzo=schizzo,
    )
    checks = tuple(c for v in ribaltamento_scorrimento for c in (v.verifica_ribaltamento, v.verifica_scorrimento))
    return success(data, inputs, checks=checks, warnings=(AVVISO_CAPACITA_PORTANTE,))


TOOLS = (
    Tool(
        name="muro-sostegno",
        title="Muro di sostegno a mensola",
        group="Geotecnica / Muri di sostegno",
        norm="NTC2018 §6.5.3.1.1, §6.5.3.1.2, §6.4.2.1, §7.11.6.2.1, §4.1.2",
        input_model=MuroSostegnoInput,
        output_model=MuroSostegnoOutput,
        run=run_muro_sostegno,
        example=ESEMPIO_TRATTO_A,
        summary="Verifica un muro di sostegno a mensola a ribaltamento, scorrimento, pressione sul terreno e armatura, per le 8 combinazioni di carico statiche e sismiche.",
    ),
)

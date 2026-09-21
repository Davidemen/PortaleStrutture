"""Frozen output models for `acciaio-colonna-h-ec3`, grouped as in acciaio-colonne-ec3!Column check."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check


class Materiali(BaseModel):
    """Grado, resistenze di progetto e coefficienti parziali (H11:H15, Materiali!H19:J23)."""

    model_config = ConfigDict(frozen=True)

    grado: str = Field(description="Grado dell'acciaio")
    fyk_MPa: float = Field(description="Tensione caratteristica di snervamento (da tabella)", json_schema_extra={"unit": "MPa", "symbol": "f_yk"})
    fuk_MPa: float = Field(description="Tensione caratteristica di rottura (da tabella)", json_schema_extra={"unit": "MPa", "symbol": "f_uk"})
    fyd_MPa: float = Field(description="Tensione di calcolo di snervamento, usata in tutte le verifiche di resistenza", json_schema_extra={"unit": "MPa", "symbol": "f_yd"})
    fud_MPa: float = Field(description="Tensione di calcolo a rottura (valore non impiegato nelle verifiche seguenti)", json_schema_extra={"unit": "MPa", "symbol": "f_ud"})
    gamma_m0: float = Field(description="Fattore parziale di sicurezza per la resistenza delle sezioni, risolto", gt=0, json_schema_extra={"unit": "-", "symbol": "γ_M0"})
    gamma_m1: float = Field(description="Fattore parziale di sicurezza per la resistenza all'instabilità, risolto", gt=0, json_schema_extra={"unit": "-", "symbol": "γ_M1"})
    gamma_m2: float = Field(description="Fattore parziale di sicurezza per la resistenza a rottura", gt=0, json_schema_extra={"unit": "-", "symbol": "γ_M2"})


class Sezione(BaseModel):
    """Grandezze derivate dalla sezione e curve di instabilità (§5.5 Tab. 5.2, §6.3.1 Tab. 6.1/6.2)."""

    model_config = ConfigDict(frozen=True)

    av_z_mm2: float = Field(description="Area resistente a taglio dell'anima Av,z (P9)", json_schema_extra={"unit": "mm2"})
    av_y_mm2: float = Field(description="Area resistente a taglio delle ali Av,y (P12)", json_schema_extra={"unit": "mm2"})
    iw_mm6: float = Field(description="Costante di ingobbamento Iw (AI10)", json_schema_extra={"unit": "mm6"})
    g_MPa: float = Field(description="Modulo di elasticità tangenziale G (AI9)", json_schema_extra={"unit": "MPa"})
    wy: float = Field(description="Rapporto Wpl,y/Wel,y limitato a 1.5 (AI28)")
    wz: float = Field(description="Rapporto Wpl,z/Wel,z limitato a 1.5 (AN28)")
    i0_quadro_mm2: float = Field(description="iy^2+iz^2 (AV41)", json_schema_extra={"unit": "mm2"})
    npl_kN: float = Field(description="Resistenza plastica assiale di progetto Npl=A*fyd (Q41)", json_schema_extra={"unit": "kN"})
    mpl_y_kNm: float = Field(description="Momento resistente di progetto per l'interazione (Q39/AD35)", json_schema_extra={"unit": "kNm"})
    mpl_z_kNm: float = Field(description="Momento resistente di progetto per l'interazione (Q40/AD36)", json_schema_extra={"unit": "kNm"})
    npl_rk_kN: float = Field(description="Resistenza plastica assiale caratteristica NRk=A*fyk, per eq. 6.61/6.62 (§6.3.3)", json_schema_extra={"unit": "kN"})
    mpl_y_rk_kNm: float = Field(description="Momento resistente caratteristico MRk,y, per eq. 6.61/6.62 (§6.3.3)", json_schema_extra={"unit": "kNm"})
    mpl_z_rk_kNm: float = Field(description="Momento resistente caratteristico MRk,z, per eq. 6.61/6.62 (§6.3.3)", json_schema_extra={"unit": "kNm"})
    alpha_lt_torsione: float = Field(description="aLT = MAX(1-IT/Iyy,0) (AI24)")
    curva_instabilita_lt: str = Field(description="Curva di instabilità flesso-torsionale (BC17, Tab. 6.3-like)")
    curva_flessionale_yy: str = Field(description="Curva di instabilità flessionale asse yy (Tab. 6.2)")
    curva_flessionale_zz: str = Field(description="Curva di instabilità flessionale asse zz (Tab. 6.2)")
    alpha_yy: float = Field(description="Fattore di imperfezione alpha per l'asse yy (Y25/Tab. 6.1)")
    alpha_zz: float = Field(description="Fattore di imperfezione alpha per l'asse zz (Y26/Tab. 6.1)")
    alpha_lt: float = Field(description="Fattore di imperfezione alpha per l'instabilità flesso-torsionale (BC25)")


class InstabilitaFlessionale(BaseModel):
    """Instabilità per flessione semplice, §6.3.1."""

    model_config = ConfigDict(frozen=True)

    ncr_y_kN: float = Field(description="Carico critico euleriano Ncr,y (Y21)", json_schema_extra={"unit": "kN"})
    ncr_z_kN: float = Field(description="Carico critico euleriano Ncr,z (Y22)", json_schema_extra={"unit": "kN"})
    ncr_t_kN: float = Field(description="Carico critico torsionale Ncr,T (AV38)", json_schema_extra={"unit": "kN"})
    lambda_yy: float = Field(description="Snellezza adimensionale lambda_yy (W23)")
    lambda_zz: float = Field(description="Snellezza adimensionale lambda_zz (W24)")
    lambda_max: float = Field(description="MAX(lambda_yy, lambda_zz) (AI33)")
    phi_yy: float = Field(description="phi per la curva di instabilità yy (W27)")
    phi_zz: float = Field(description="phi per la curva di instabilità zz (W28)")
    chi_yy: float = Field(description="Fattore riduttivo chi_yy (W29)")
    chi_zz: float = Field(description="Fattore riduttivo chi_zz (W32)")


class InstabilitaTorsoFlessionale(BaseModel):
    """Instabilità flesso-torsionale (LTB), §6.3.2."""

    model_config = ConfigDict(frozen=True)

    mcr_Nmm: float = Field(description="Momento critico elastico Mcr (AI8)", json_schema_extra={"unit": "Nmm"})
    lambda_lt: float = Field(description="Snellezza adimensionale lambda_LT (S34/AI35)")
    phi_lt: float = Field(description="phi_LT (W36)")
    chi_lt: float = Field(description="Fattore riduttivo chi_LT (U37)")
    verifica_non_necessaria: bool = Field(description="LTB non necessaria per §6.3.2.2(4) (O59)")


class Flessione(BaseModel):
    """Resistenza a flessione, §6.2.5, con riduzione per taglio elevato §6.2.8."""

    model_config = ConfigDict(frozen=True)

    fy_ridotta_y_MPa: float = Field(description="fy' per MRd,y, ridotta se il taglio è elevato (G31)", json_schema_extra={"unit": "MPa"})
    fy_ridotta_z_MPa: float = Field(description="fy' per MRd,z, ridotta se il taglio è elevato (G41)", json_schema_extra={"unit": "MPa"})
    mrd_y_kNm: float = Field(description="Momento resistente, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,y"})
    mrd_z_kNm: float = Field(description="Momento resistente, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,z"})
    verifica_y: Check
    verifica_z: Check


class Taglio(BaseModel):
    """Resistenza a taglio, §6.2.6."""

    model_config = ConfigDict(frozen=True)

    vpl_rd_anima_kN: float = Field(description="Resistenza a taglio dell'anima", json_schema_extra={"unit": "kN", "symbol": "V_pl,Rd"})
    vpl_rd_ali_kN: float = Field(description="Resistenza a taglio delle ali", json_schema_extra={"unit": "kN", "symbol": "V_pl,Rd"})
    verifica_anima: Check
    verifica_ali: Check


class TaglioInstabilita(BaseModel):
    """Instabilità per taglio dell'anima, §6.2.6(6)/EN1993-1-5 §5."""

    model_config = ConfigDict(frozen=True)

    hw_t: float = Field(description="Snellezza dell'anima hw/tw (AC27)")
    limite_72_eps_eta: float = Field(description="Limite 72*epsilon*eta (AD27)")
    richiede_verifica: bool = Field(description="hw/tw > limite -> verifica richiesta (K32)")
    cw: float = Field(description="Coefficiente di imbozzamento cw (C67)")
    vb_rd_kN: float = Field(description="Resistenza a taglio per instabilità dell'anima", json_schema_extra={"unit": "kN", "symbol": "V_b,Rd"})
    verifica: Check


class Interazione(BaseModel):
    """Interazione N-My-Mz, Annex A, eq. 6.61/6.62."""

    model_config = ConfigDict(frozen=True)

    cmy: float = Field(description="Fattore di momento uniforme equivalente Cmy (AM64)")
    cmz: float = Field(description="Fattore di momento uniforme equivalente Cmz (AM65)")
    cm_lt: float = Field(description="Fattore CmLT (AM66)")
    kyy: float = Field(description="Fattore di interazione kyy (X42)")
    kyz: float = Field(description="Fattore di interazione kyz (X43)")
    kzy: float = Field(description="Fattore di interazione kzy (X44)")
    kzz: float = Field(description="Fattore di interazione kzz (X45)")
    utilizzo_yy: float = Field(description="Rapporto di utilizzo dell'interazione N-My-Mz, asse forte", json_schema_extra={"unit": "-", "symbol": "N/N_Rd+...", "highlight": True})
    utilizzo_zz: float = Field(description="Rapporto di utilizzo dell'interazione N-My-Mz, asse debole", json_schema_extra={"unit": "-", "symbol": "N/N_Rd+...", "highlight": True})
    verifica_yy: Check
    verifica_zz: Check


class InterazioneSemplificata(BaseModel):
    """Verifiche semplificate di riscontro (fallback), non da Annex A."""

    model_config = ConfigDict(frozen=True)

    n_ratio: float = Field(description="n = Nsd/Npl (H46)")
    mn_rd_y_kNm: float = Field(description="Momento resistente ridotto per la presenza di sforzo normale, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_N,Rd,y"})
    mn_rd_z_kNm: float = Field(description="Momento resistente ridotto per la presenza di sforzo normale, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_N,Rd,z"})
    verifica_yy: Check
    verifica_zz: Check
    v54: float = Field(description="Somma dei rapporti di utilizzo lineari (V54)")
    verifica_lineare: Check
    i56: float = Field(description="Interazione a potenza (I56)")
    verifica_potenza: Check


class ColonnaEc3Output(BaseModel):
    """Esito completo della verifica di colonna in acciaio a sezione H/I, EN1993-1-1."""

    model_config = ConfigDict(frozen=True)

    materiali: Materiali
    sezione: Sezione
    instabilita_flessionale: InstabilitaFlessionale
    instabilita_torso_flessionale: InstabilitaTorsoFlessionale
    flessione: Flessione
    taglio: Taglio
    taglio_instabilita: TaglioInstabilita
    interazione: Interazione
    interazione_semplificata: InterazioneSemplificata

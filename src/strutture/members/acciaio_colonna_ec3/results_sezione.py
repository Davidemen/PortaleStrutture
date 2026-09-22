"""Materiali/Sezione output models, split out of `results.py` (regola dura 12)."""
from pydantic import BaseModel, ConfigDict, Field


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

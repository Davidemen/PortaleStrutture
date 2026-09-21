"""Composes one `carichi` row into its full `pav-carichi-concentrati` result (spec calculation steps
1-13, repeated identically for every row -- the sheet's separate "ruota motrice"/"ruote anteriori"
blocks become rows of the same table, architecture-batch2.md §2). Flat row model so it doubles as the
CSV-exportable `righe` entry (architecture-batch2.md §2 "many-rows results")."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014

from .carico_row import CaricoRow
from .concentrati_contatto import contatto
from .concentrati_punzonamento import punzonamento
from .concentrati_tensioni import sigma_westergaard, tensioni
from .tables import CRACK_DERATING_FACTOR


class RigaCaricoResult(BaseModel):
    """One row of `pav-carichi-concentrati` (key columns echoed, then every derived quantity)."""

    model_config = ConfigDict(frozen=True)

    caso: str = Field(description="Nome del caso di carico")
    posizione: str = Field(description="Posizione del carico sulla piastra")
    ac_mm2: float = Field(description="Area di contatto Ac", json_schema_extra={"unit": "mm2", "symbol": "A_c"})
    b_mm: float = Field(description="Raggio di contatto corretto b", json_schema_extra={"unit": "mm", "symbol": "b"})
    sigma_c_max_MPa: float = Field(description="Tensione di flessione ULS σc,max", json_schema_extra={"unit": "MPa", "symbol": "σ_c,max"})
    # tl_tensionale/tl_fessurazione/tl_armatura have no lower bound: the spigolo (corner) Westergaard
    # formula can turn slightly negative for a very large footprint relative to l (a genuine sheet
    # value, not a bug -- see `concentrati_tensioni.TensioniResult.sigma_c_max_MPa`).
    tl_tensionale: float = Field(description="Tasso di lavoro tensionale σc,max/fcfd", json_schema_extra={"unit": "-", "symbol": "TL_σ"})
    sigma_c_t_MPa: float = Field(description="Tensione di trazione SLE frequente σc,t", json_schema_extra={"unit": "MPa", "symbol": "σ_c,t"})
    tl_fessurazione: float = Field(description="Tasso di lavoro a fessurazione σc,t/(fctm/1.2)", json_schema_extra={"unit": "-", "symbol": "TL_f"})
    m_slu_Nmm_m: float = Field(description="Momento nominale ULS M_SLU", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLU"})
    tl_armatura: float = Field(description="Tasso di lavoro dell'armatura M_SLU/Mrd", json_schema_extra={"unit": "-", "symbol": "TL_As"})
    v_ed_kN: float = Field(description="Azione di taglio per punzonamento VEd", json_schema_extra={"unit": "kN", "symbol": "V_Ed"})
    u1_mm: float = Field(description="Perimetro di verifica a distanza 2d u1", json_schema_extra={"unit": "mm", "symbol": "u_1"})
    tl_punzonamento_u0: float = Field(description="Tasso di lavoro a punzonamento a u0", ge=0, json_schema_extra={"unit": "-", "symbol": "TL_u0"})
    tl_punzonamento_u1: float = Field(description="Tasso di lavoro a punzonamento a u1", ge=0, json_schema_extra={"unit": "-", "symbol": "TL_u1"})
    utilizzo_max: float = Field(
        description="Massimo tasso di lavoro della riga (governa la selezione dell'inviluppo)", ge=0,
        json_schema_extra={"unit": "-", "symbol": "TL_max", "highlight": True},
    )


def riga_carico(
    riga: CaricoRow, h_mm: float, l_mm: float, fcfd_MPa: float, fctm_MPa: float, mrd_Nmm_m: float,
    d_mm: float, v1: float, fcd_MPa: float, v_min_MPa: float, *, legacy_compat: bool = False,
    coeff_vrd_max: float = V_RD_MAX_COEFF_A1_2014,
) -> RigaCaricoResult:
    """One full pass of spec steps 1-13 for a single `carichi` row."""
    contatto_result = contatto(riga.impronta_a_mm, riga.impronta_b_mm, h_mm)
    tensioni_result = tensioni(
        riga.posizione, riga.p_kN, riga.gamma, riga.psi1, h_mm, l_mm, contatto_result.b_mm, contatto_result.rr_mm,
    )
    sigma_t = sigma_westergaard(
        riga.posizione, tensioni_result.p_sle_freq_kN, h_mm, l_mm, contatto_result.b_mm, contatto_result.rr_mm,
    )
    punzonamento_result = punzonamento(
        riga.posizione, tensioni_result.p_slu_kN, riga.impronta_a_mm, riga.impronta_b_mm,
        d_mm, h_mm, v1, fcd_MPa, v_min_MPa, legacy_compat=legacy_compat, coeff_vrd_max=coeff_vrd_max,
    )
    tl_tensionale = tensioni_result.sigma_c_max_MPa / fcfd_MPa
    tl_fessurazione = sigma_t / (fctm_MPa / CRACK_DERATING_FACTOR)
    tl_armatura = tensioni_result.m_slu_Nmm_m / mrd_Nmm_m
    tl_u0 = punzonamento_result.v_ed0_MPa / punzonamento_result.v_rd_max_MPa
    tl_u1 = punzonamento_result.v_ed1_MPa / punzonamento_result.v_rd_c_MPa
    return RigaCaricoResult(
        caso=riga.caso, posizione=riga.posizione, ac_mm2=contatto_result.ac_mm2, b_mm=contatto_result.b_mm,
        sigma_c_max_MPa=tensioni_result.sigma_c_max_MPa, tl_tensionale=tl_tensionale,
        sigma_c_t_MPa=sigma_t, tl_fessurazione=tl_fessurazione,
        m_slu_Nmm_m=tensioni_result.m_slu_Nmm_m, tl_armatura=tl_armatura,
        v_ed_kN=punzonamento_result.v_ed_kN, u1_mm=punzonamento_result.u1_mm,
        tl_punzonamento_u0=tl_u0, tl_punzonamento_u1=tl_u1,
        utilizzo_max=max(tl_tensionale, tl_fessurazione, tl_armatura, tl_u0, tl_u1),
    )

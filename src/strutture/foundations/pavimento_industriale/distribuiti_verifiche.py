"""Stress, crack and reinforcement checks for `pav-carichi-distribuiti` (spec calculation steps
6-12). Divergence (architecture-batch2.md §7 `pavimento G22`, spec bug 1): the sheet checks the
top-fibre ULS stress against `fcfk` (characteristic) but the bottom fibre against `fcfd` (design) --
the same sup/inf check pair should use the same strength basis. `legacy_compat=True` reproduces the
sheet (`fcfk` sup); `legacy_compat=False` uses `fcfd` for both, per every other check on the sheet."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

from .tables import CRACK_DERATING_FACTOR

MPA_UNIT_FIX = 1000.0  # spec steps 6/8: moment [Nmm/m] / W [mm3/m] * 1000 -> MPa.


class VerificheDistribuitoResult(BaseModel):
    """`pav-carichi-distribuiti` outputs G21/H21, G22/H22, G26/H26, G27/H27, G35/H35."""

    model_config = ConfigDict(frozen=True)

    sigma_c_max_sup_MPa: float = Field(description="Tensione di flessione ULS, fibra superiore", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,max,sup"})
    sigma_c_max_inf_MPa: float = Field(description="Tensione di flessione ULS, fibra inferiore", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,max,inf"})
    verifica_tensionale_sup: Check
    verifica_tensionale_inf: Check
    sigma_c_t_sup_MPa: float = Field(description="Tensione di trazione SLE frequente, fibra superiore", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,t,sup"})
    sigma_c_t_inf_MPa: float = Field(description="Tensione di trazione SLE frequente, fibra inferiore", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,t,inf"})
    verifica_fessurazione_sup: Check
    verifica_fessurazione_inf: Check
    verifica_armatura_sup: Check
    verifica_armatura_inf: Check
    tl_massimo: float = Field(
        description="Massimo tasso di lavoro fra tutte le verifiche del carico distribuito", ge=0,
        json_schema_extra={"unit": "-", "symbol": "TL_max", "highlight": True},
    )


def _check(name: str, value: float, limit: float, clause: str) -> Check:
    return Check(name=name, passed=value <= limit, clause=clause, value=value, limit=limit, unit="-")


def _tasso(check: Check) -> float:
    return check.value / check.limit


def verifiche_distribuito(
    m_slu_sup_Nmm_m: float, m_slu_inf_Nmm_m: float,
    m_sle_freq_sup_Nmm_m: float, m_sle_freq_inf_Nmm_m: float,
    w_mm3_m: float, fcfk_MPa: float, fcfd_MPa: float, fctm_MPa: float, mrd_Nmm_m: float,
    *, legacy_compat: bool = False,
) -> VerificheDistribuitoResult:
    """spec steps 6-12."""
    sigma_max_sup = m_slu_sup_Nmm_m / w_mm3_m * MPA_UNIT_FIX
    sigma_max_inf = m_slu_inf_Nmm_m / w_mm3_m * MPA_UNIT_FIX
    sigma_t_sup = m_sle_freq_sup_Nmm_m / w_mm3_m * MPA_UNIT_FIX
    sigma_t_inf = m_sle_freq_inf_Nmm_m / w_mm3_m * MPA_UNIT_FIX
    fcfd_sup = fcfk_MPa if legacy_compat else fcfd_MPa
    fessurazione_limite = fctm_MPa / CRACK_DERATING_FACTOR
    checks = (
        _check("Verifica tensionale ULS, sup", sigma_max_sup, fcfd_sup, "CNR-DT211/2014"),
        _check("Verifica tensionale ULS, inf", sigma_max_inf, fcfd_MPa, "CNR-DT211/2014"),
        _check("Verifica a fessurazione, sup", sigma_t_sup, fessurazione_limite, "CNR-DT211/2014"),
        _check("Verifica a fessurazione, inf", sigma_t_inf, fessurazione_limite, "CNR-DT211/2014"),
        _check("Verifica armatura minima, sup", m_slu_sup_Nmm_m, mrd_Nmm_m, "CNR-DT211/2014"),
        _check("Verifica armatura minima, inf", m_slu_inf_Nmm_m, mrd_Nmm_m, "CNR-DT211/2014"),
    )
    tensionale_sup, tensionale_inf, fessurazione_sup, fessurazione_inf, armatura_sup, armatura_inf = checks
    return VerificheDistribuitoResult(
        sigma_c_max_sup_MPa=sigma_max_sup, sigma_c_max_inf_MPa=sigma_max_inf,
        verifica_tensionale_sup=tensionale_sup, verifica_tensionale_inf=tensionale_inf,
        sigma_c_t_sup_MPa=sigma_t_sup, sigma_c_t_inf_MPa=sigma_t_inf,
        verifica_fessurazione_sup=fessurazione_sup, verifica_fessurazione_inf=fessurazione_inf,
        verifica_armatura_sup=armatura_sup, verifica_armatura_inf=armatura_inf,
        tl_massimo=max(_tasso(c) for c in checks),
    )

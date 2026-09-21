"""Winkler subgrade + slab plate-stiffness for `pav-fondazione-materiali` (spec calculation steps
10-17): reuses `shared.ec2_shear.k_size`/`v_min` for the EC2 §6.2.2 shear-size terms that this sheet
also needs for its punching checks, and `shared.tables.exact_lookup` for the `Winkler` table."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ec2_shear import k_size, v_min
from strutture.shared.tables import exact_lookup

from .tables import WINKLER_K_PRIME_N_MM3, SottofondoTipo

NU_COEFFICIENT = 0.6  # EC2 6.2.2 v1 = 0.6*(1 - fck/250) (spec step 17).
FCK_LIMIT_FOR_NU = 250.0


class SottofondoResult(BaseModel):
    """`pav-fondazione-materiali` outputs C26/C29-C35 (subgrade + plate stiffness + EC2 shear terms)."""

    model_config = ConfigDict(frozen=True)

    kt_N_mm3: float = Field(description="Modulo di reazione del sottofondo (Winkler k')", gt=0, json_schema_extra={"unit": "N/mm3", "symbol": "k_T"})
    d_mm: float = Field(description="Altezza utile della piastra d = h - c", gt=0, json_schema_extra={"unit": "mm", "symbol": "d"})
    lambda_mm1: float = Field(description="Parametro di rigidezza della piastra λ", gt=0, json_schema_extra={"unit": "1/mm", "symbol": "λ"})
    w_mm3_m: float = Field(description="Modulo di resistenza a flessione, striscia di 1 m W", gt=0, json_schema_extra={"unit": "mm3/m", "symbol": "W"})
    l_mm: float = Field(description="Raggio di rigidezza relativa di Westergaard l", gt=0, json_schema_extra={"unit": "mm", "symbol": "l", "highlight": True})
    k_ec2: float = Field(description="Fattore di scala EC2 §6.2.2 k = min(1+sqrt(200/d), 2)", gt=0, le=2, json_schema_extra={"symbol": "k"})
    v_min_MPa: float = Field(description="Tensione minima di taglio EC2 §6.2.2 vmin", gt=0, json_schema_extra={"unit": "MPa", "symbol": "v_min"})
    v1: float = Field(description="Fattore di riduzione EC2 §6.2.2 v1 = 0.6*(1-fck/250)", gt=0, json_schema_extra={"symbol": "ν_1"})


def sottofondo(
    h_mm: float,
    c_mm: float,
    nu_poisson: float,
    ecm_MPa: float,
    fck_MPa: float,
    *,
    sottofondo_tipo: SottofondoTipo | None,
    kt_manuale_N_mm3: float | None,
) -> SottofondoResult:
    """`pav-fondazione-materiali` steps 10-17. Exactly one of `sottofondo_tipo` (`Winkler!A2:C5`
    lookup) or `kt_manuale_N_mm3` (direct override) is expected -- enforced by the input model."""
    if sottofondo_tipo is None and kt_manuale_N_mm3 is None:
        raise ValueError("indicare sottofondo_tipo oppure kt_manuale_N_mm3")
    kt_n_mm3 = kt_manuale_N_mm3 if sottofondo_tipo is None else exact_lookup(WINKLER_K_PRIME_N_MM3, sottofondo_tipo)
    d_mm = h_mm - c_mm
    lambda_mm1 = (3.0 * kt_n_mm3 / (ecm_MPa * h_mm**3)) ** 0.25
    w_mm3_m = 1000.0 * h_mm**2 / 6.0
    l_mm = ((ecm_MPa * h_mm**3) / (12.0 * (1.0 - nu_poisson**2) * kt_n_mm3)) ** 0.25
    k_ec2 = k_size(d_mm)
    v_min_mpa = v_min(k_ec2, fck_MPa)
    v1 = NU_COEFFICIENT * (1.0 - fck_MPa / FCK_LIMIT_FOR_NU)
    return SottofondoResult(
        kt_N_mm3=kt_n_mm3, d_mm=d_mm, lambda_mm1=lambda_mm1, w_mm3_m=w_mm3_m,
        l_mm=l_mm, k_ec2=k_ec2, v_min_MPa=v_min_mpa, v1=v1,
    )

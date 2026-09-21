"""Step: transfer of one load combination's column-top forces to final base moments at pile-head
level (docs/specs/fond-plinti-pali.md Tool-1 steps 2-4, `Footing check!S,T,U,V,W,X`).

`Mx,final`/`My,final` do not depend on the pile pattern (only on the plinth height and the user's
load eccentricity `ex`/`ey`), so this step is shared by both `legacy_compat` branches of
`pali_riga.py`: the sheet's own per-pile-share formula (steps 1, 6-7) and the fixed
`shared.pile_group.rigid_cap_axial` path both start from the same `Mx,final`/`My,final`."""
from pydantic import BaseModel, ConfigDict, Field


class MomentiPila(BaseModel):
    """Final Mx/My at pile-head level, after the shear lever arm and the load eccentricity."""

    model_config = ConfigDict(frozen=True)

    mx_finale_kNm: float = Field(description="Momento Mx finale in testa ai pali", json_schema_extra={"unit": "kNm"})
    my_finale_kNm: float = Field(description="Momento My finale in testa ai pali", json_schema_extra={"unit": "kNm"})


def momenti_pila(
    fx_kN: float, fy_kN: float, fz_kN: float, mx_kNm: float, my_kNm: float,
    h_plinto_m: float, ex_m: float, ey_m: float,
) -> MomentiPila:
    """`Mx,final = Mx + N*ey - Fy*H`, `My,final = My - N*ex + Fx*H` (H = plinth height, the shear's
    lever arm to the pile head; `ex`/`ey` transfer `N` through the user's load eccentricity)."""
    return MomentiPila(
        mx_finale_kNm=mx_kNm + fz_kN * ey_m - fy_kN * h_plinto_m,
        my_finale_kNm=my_kNm - fz_kN * ex_m + fx_kN * h_plinto_m,
    )

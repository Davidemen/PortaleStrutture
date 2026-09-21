"""Step 2: net design pressure q' = q − γ·D (docs/specs/geo-cedimenti-edometrico.md, calculation
step 1: `B12[q'] = B11[q] − B3[γ]·0.0001·B8`; the 0.0001 was the sheet's cm/kg-cm² unit factor
against a cm-embedment cell, already folded into `ingresso.py`'s boundary conversion here).

docs/architecture-batch2.md §7 review finding MEDIUM: the overburden relief must use the same
effective-weight/water-table basis as `righe.sigma_v0_kPa` (not always the total weight), and a
non-positive q' must fail fast here rather than propagate a negative settlement down every
downstream step. `legacy_compat=True` keeps the sheet's own `γ·D` formula, water table ignored —
frozen, see `docs/divergences/geo-cedimenti-edometrico.md`."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import CalcError
from strutture.shared.soil_layers import effective_overburden


class CaricoResult(BaseModel):
    """q, the overburden removed by the embedment, and the resulting net design pressure q'."""

    model_config = ConfigDict(frozen=True)

    q_kPa: float = Field(description="Pressione di contatto applicata q", json_schema_extra={"unit": "kPa", "symbol": "q"})
    sovraccarico_rimosso_kPa: float = Field(
        description="Sovraccarico rimosso dallo scavo/infissione, γ·D (o γ efficace sotto falda)",
        json_schema_extra={"unit": "kPa", "symbol": "γ·D"},
    )
    q_prime_kPa: float = Field(description="Pressione netta di progetto q' = q − γ·D", json_schema_extra={"unit": "kPa", "symbol": "q'"})


def pressione_netta(
    q_kPa: float,
    gamma_kN_m3: float,
    d_m: float,
    *,
    water_table_m: float | None = None,
    legacy_compat: bool = False,
) -> CaricoResult:
    """`water_table_m=None` (default) = dry site, plain total weight `γ·D` — identical to
    `legacy_compat=True` unless an explicit water table is given. In `legacy_compat=True`,
    `water_table_m` is always ignored (sheet's own formula, frozen)."""
    if legacy_compat:
        sovraccarico_kPa = gamma_kN_m3 * d_m
    else:
        riferimento_falda_m = water_table_m if water_table_m is not None else float("inf")
        sovraccarico_kPa = effective_overburden(gamma_kN_m3, d_m, water_table_m=riferimento_falda_m)
    q_prime_kPa = q_kPa - sovraccarico_kPa
    if q_prime_kPa <= 0:
        raise CalcError(
            f"pressione netta q' = q − γ·D non positiva (q={q_kPa:g} kPa, γ={gamma_kN_m3:g} kN/m³, "
            f"D={d_m:g} m): lo scavo/infissione rimuove più sovraccarico di quanto applicato dalla fondazione"
        )
    return CaricoResult(q_kPa=q_kPa, sovraccarico_rimosso_kPa=sovraccarico_kPa, q_prime_kPa=q_prime_kPa)

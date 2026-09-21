"""Composes the `carichi` table into `pav-carichi-concentrati`'s many-rows result (architecture-
batch2.md §2 "many-rows results": `righe`, `inviluppo`, `governante`; `checks` on the envelope only,
never one check per row)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.report import Check

from .carico_row import CaricoRow
from .concentrati_riga import RigaCaricoResult, riga_carico

GRANDEZZE = (
    ("tl_tensionale", "Tensionale (Westergaard)", "Verifica tensionale, carico concentrato", "CNR-DT211/2014"),
    ("tl_fessurazione", "Fessurazione", "Verifica a fessurazione, carico concentrato", "CNR-DT211/2014"),
    ("tl_armatura", "Armatura", "Verifica armatura minima, carico concentrato", "CNR-DT211/2014"),
    ("tl_punzonamento_u0", "Punzonamento a u0", "Punzonamento a u0, carico concentrato", "EC2 §6.4.5"),
    ("tl_punzonamento_u1", "Punzonamento a u1", "Punzonamento a u1, carico concentrato", "EC2 §6.4.4"),
)


class EnvelopeRow(BaseModel):
    """One quantity's governing (worst) value across every `carichi` row."""

    model_config = ConfigDict(frozen=True)

    grandezza: str = Field(description="Grandezza inviluppata")
    valore: float = Field(description="Valore governante (massimo tasso di lavoro)", ge=0, json_schema_extra={"unit": "-"})
    caso: str = Field(description="Caso di carico governante")
    posizione: str = Field(description="Posizione governante")


class ConcentratiResult(BaseModel):
    """`pav-carichi-concentrati`: per-row results + envelope + governing row."""

    model_config = ConfigDict(frozen=True)

    righe: tuple[RigaCaricoResult, ...] = Field(description="Risultati per ogni riga della tabella carichi", json_schema_extra={"rows_page": 200})
    inviluppo: tuple[EnvelopeRow, ...] = Field(description="Valore governante di ogni verifica sulle righe")
    governante: RigaCaricoResult = Field(description="Riga con il tasso di lavoro complessivo massimo")


def concentrati(
    carichi: tuple[CaricoRow, ...], h_mm: float, l_mm: float, fcfd_MPa: float, fctm_MPa: float,
    mrd_Nmm_m: float, d_mm: float, v1: float, fcd_MPa: float, v_min_MPa: float, *, legacy_compat: bool = False,
    coeff_vrd_max: float = V_RD_MAX_COEFF_A1_2014,
) -> tuple[ConcentratiResult, tuple[Check, ...]]:
    """Runs `riga_carico` for every row and builds the envelope + governing-row result + checks."""
    righe = tuple(
        riga_carico(
            riga, h_mm, l_mm, fcfd_MPa, fctm_MPa, mrd_Nmm_m, d_mm, v1, fcd_MPa, v_min_MPa,
            legacy_compat=legacy_compat, coeff_vrd_max=coeff_vrd_max,
        )
        for riga in carichi
    )
    inviluppo = tuple(
        _envelope_row(righe, campo, nome) for campo, nome, _, _ in GRANDEZZE
    )
    governante = max(righe, key=lambda r: r.utilizzo_max)
    checks = tuple(
        Check(name=descrizione, passed=valore <= 1.0, clause=clausola, value=valore, limit=1.0, unit="-")
        for (_, _, descrizione, clausola), valore in zip(GRANDEZZE, (row.valore for row in inviluppo), strict=True)
    )
    return ConcentratiResult(righe=righe, inviluppo=inviluppo, governante=governante), checks


def _envelope_row(righe: tuple[RigaCaricoResult, ...], campo: str, nome: str) -> EnvelopeRow:
    governante = max(righe, key=lambda r: getattr(r, campo))
    return EnvelopeRow(grandezza=nome, valore=getattr(governante, campo), caso=governante.caso, posizione=governante.posizione)

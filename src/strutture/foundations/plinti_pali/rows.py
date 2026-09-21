"""Composes one `reazioni` row (one load combination, "LCC") into its per-pile axial demand
(docs/specs/fond-plinti-pali.md Tool-1). Pure composition of `azioni_pila` + `shared.pile_group`;
no formulas of its own besides the `legacy_compat` per-pile-share reproduction (steps 1, 6-7).

Fix (docs/architecture-batch2.md §9-D5): `shared.pile_group.rigid_cap_axial` gives the exact axial
reaction of every actual pile from its coordinates, generalising the sheet's own formula (valid only
for its 4 symmetric grids, see the module's own docstring) to any pile pattern; `legacy_compat=True`
reproduces the sheet's per-pile-share formula instead, which reports one Nmin/Nmax pair per row
rather than a value per pile (`AB`/`AC`)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.divergences import legacy
from strutture.shared.load_table import Famiglia, ReactionRow
from strutture.shared.pile_group import PilePos, rigid_cap_axial

from .azioni_pila import momenti_pila


class RigaCarico(BaseModel):
    """Per-pile axial demand of one load combination (key columns echoed for the `righe` result)."""

    model_config = ConfigDict(frozen=True)

    nodo: int = Field(description="Nodo della struttura", json_schema_extra={"unit": "-"})
    combo: str = Field(description="Nome della combinazione di carico (LCC)", json_schema_extra={"unit": "-"})
    famiglia: Famiglia | None = Field(description="Famiglia della combinazione (assente = un inviluppo globale)",
                                       json_schema_extra={"unit": "-"})
    n_kN: float = Field(description="Carico verticale totale in colonna N", json_schema_extra={"unit": "kN"})
    mx_finale_kNm: float = Field(description="Momento Mx finale in testa ai pali", json_schema_extra={"unit": "kNm"})
    my_finale_kNm: float = Field(description="Momento My finale in testa ai pali", json_schema_extra={"unit": "kNm"})
    n_pali_kN: tuple[float, ...] = Field(description="Reazione assiale di ogni palo, stesso ordine dello schema",
                                          json_schema_extra={"unit": "kN"})
    n_min_pila_kN: float = Field(description="Reazione assiale minima tra i pali di questa combinazione",
                                  json_schema_extra={"unit": "kN"})
    n_max_pila_kN: float = Field(description="Reazione assiale massima tra i pali di questa combinazione",
                                  json_schema_extra={"unit": "kN"})


def riga_carico(
    row: ReactionRow, piles: tuple[PilePos, ...], count_x: int, count_y: int,
    lx_m: float, ly_m: float, h_plinto_m: float, ex_m: float, ey_m: float, *, legacy_compat: bool,
) -> RigaCarico:
    """Full per-pile axial demand of one `reazioni` row."""
    momenti = momenti_pila(row.fx_kN, row.fy_kN, row.fz_kN, row.mx_kNm, row.my_kNm, h_plinto_m, ex_m, ey_m)
    n_pali = rigid_cap_axial(row.fz_kN, momenti.mx_finale_kNm, momenti.my_finale_kNm, piles)
    if legacy("plinti-pali/quota-pila-formula-simmetrica-non-generale", legacy_compat):
        n_min, n_max = _quota_per_palo_legacy(row.fz_kN, momenti, len(piles), count_x, count_y, lx_m, ly_m)
    else:
        n_min, n_max = min(n_pali), max(n_pali)
    return RigaCarico(
        nodo=row.nodo, combo=row.combo, famiglia=row.famiglia, n_kN=row.fz_kN,
        mx_finale_kNm=momenti.mx_finale_kNm, my_finale_kNm=momenti.my_finale_kNm,
        n_pali_kN=n_pali, n_min_pila_kN=n_min, n_max_pila_kN=n_max,
    )


def _quota_per_palo_legacy(
    n_kN: float, momenti, numero_pali: int, count_x: int, count_y: int, lx_m: float, ly_m: float,
) -> tuple[float, float]:
    """Sheet's own `AB`/`AC` (steps 1, 6-7): one symmetric-grid Nmin/Nmax pair per row, valid only
    when every pile carries the same axial share of `N` (the sheet's 4 supported grids)."""
    quota = n_kN / numero_pali
    extra_da_my = abs((momenti.my_finale_kNm / lx_m) / count_y) if lx_m > 0 else 0.0
    extra_da_mx = abs((momenti.mx_finale_kNm / ly_m) / count_x) if ly_m > 0 else 0.0
    return quota - extra_da_my - extra_da_mx, quota + extra_da_my + extra_da_mx

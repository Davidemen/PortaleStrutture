"""Composes one `reazioni` row into its full per-combination check (docs/specs/fond-plinti-isolati.md
Tool-1): self-weight -> base actions -> contact pressure -> sliding/overturning. Pure composition of
the step modules; no formulas of its own."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.footing_pressure import Metodo
from strutture.shared.load_table import Famiglia, ReactionRow
from strutture.shared.report import CalcError

from .azioni_base import azioni_base
from .gamma_azioni import gamma_permanenti
from .pesi_propri import PesiPropri, pesi_propri
from .pressione_contatto import pressione_contatto
from .ribaltamento import mu_ribaltamento
from .scorrimento import mu_scorrimento


class RigaVerifica(BaseModel):
    """Full per-combination check of one `reazioni` row (key columns echoed for the `righe` result)."""

    model_config = ConfigDict(frozen=True)

    nodo: int = Field(description="Nodo della struttura", json_schema_extra={"unit": "-"})
    combo: str = Field(description="Nome della combinazione di carico", json_schema_extra={"unit": "-"})
    famiglia: Famiglia = Field(description="Famiglia della combinazione", json_schema_extra={"unit": "-"})
    n_kN: float = Field(description="Carico verticale totale alla base N", json_schema_extra={"unit": "kN"})
    myy_kNm: float = Field(description="Momento alla base Myy", json_schema_extra={"unit": "kNm"})
    mxx_kNm: float = Field(description="Momento alla base Mxx", json_schema_extra={"unit": "kNm"})
    ex_m: float = Field(description="Eccentricità lungo X, ex = Myy/N", json_schema_extra={"unit": "m"})
    ey_m: float = Field(description="Eccentricità lungo Y, ey = Mxx/N", json_schema_extra={"unit": "m"})
    sigma_max_kpa: float = Field(description="Pressione di contatto massima", ge=0, json_schema_extra={"unit": "kPa"})
    sigma_min_kpa: float = Field(description="Pressione di contatto minima", ge=0, json_schema_extra={"unit": "kPa"})
    compressed_ratio: float = Field(description="Rapporto base reagente / base totale (1 = tutta compressa)",
                                     ge=0, le=1, json_schema_extra={"unit": "-"})
    mu_ribaltamento_x: float | None = Field(description="Coefficiente di sicurezza al ribaltamento, direzione X",
                                             json_schema_extra={"unit": "-"})
    mu_ribaltamento_y: float | None = Field(description="Coefficiente di sicurezza al ribaltamento, direzione Y",
                                             json_schema_extra={"unit": "-"})
    mu_scorrimento: float | None = Field(description="Coefficiente di sicurezza allo scorrimento",
                                          json_schema_extra={"unit": "-"})


def riga_verifica(
    row: ReactionRow, ax_m: float, by_m: float, h_plinto_m: float, h_interro_m: float,
    a_pedestal_m: float, b_pedestal_m: float, h_pedestal_sopra_m: float, h_pedestal_sotto_m: float,
    offset_leva_m: float, ex_utente_m: float, ey_utente_m: float, gamma_terreno_kNm3: float,
    phi_terreno_deg: float, *, metodo_pressioni: Metodo, legacy_compat: bool,
) -> RigaVerifica:
    """Full verification of one `reazioni` row, per docs/specs/fond-plinti-isolati.md Tool-1."""
    if row.famiglia is None:
        raise CalcError(f"combinazione '{row.combo}' (nodo {row.nodo}): la famiglia e' obbligatoria per i plinti isolati")
    pesi: PesiPropri = pesi_propri(
        ax_m, by_m, h_plinto_m, h_interro_m, a_pedestal_m, b_pedestal_m,
        h_pedestal_sopra_m, h_pedestal_sotto_m, gamma_terreno_kNm3,
    )
    gamma_w = gamma_permanenti(row.famiglia, legacy_compat=legacy_compat)
    try:
        azioni = azioni_base(row.fz_kN, row.fx_kN, row.fy_kN, row.mx_kNm, row.my_kNm, pesi, gamma_w,
                              h_plinto_m, offset_leva_m, ex_utente_m, ey_utente_m)
        pressione = pressione_contatto(azioni.n_kN, azioni.mxx_kNm, azioni.myy_kNm, ax_m, by_m,
                                        metodo_pressioni=metodo_pressioni, legacy_compat=legacy_compat)
    except (ValueError, CalcError) as error:
        raise CalcError(f"combinazione '{row.combo}' (nodo {row.nodo}): {error}") from error
    ribaltamento = mu_ribaltamento(azioni.n_kN, ax_m, by_m, azioni.myy_kNm, azioni.mxx_kNm, legacy_compat=legacy_compat)
    scorrimento = mu_scorrimento(azioni.n_kN, azioni.vx_kN, azioni.vy_kN, phi_terreno_deg, legacy_compat=legacy_compat)
    return RigaVerifica(
        nodo=row.nodo, combo=row.combo, famiglia=row.famiglia,
        n_kN=azioni.n_kN, myy_kNm=azioni.myy_kNm, mxx_kNm=azioni.mxx_kNm,
        ex_m=pressione.ex_m, ey_m=pressione.ey_m,
        sigma_max_kpa=pressione.sigma_max_kpa, sigma_min_kpa=pressione.sigma_min_kpa,
        compressed_ratio=pressione.compressed_ratio,
        mu_ribaltamento_x=ribaltamento.mu_x, mu_ribaltamento_y=ribaltamento.mu_y,
        mu_scorrimento=scorrimento,
    )

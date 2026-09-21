"""Step: NTC2018 §6.4.2.1 / EN 1997-1 Annex D bearing-capacity check of ONE `reazioni` row, from
`strutture.shared.capacita_portante` (docs/architecture-phase4.md §C "Integration"). Used only when
the optional input "Terreno" block is filled (`capacita_portante.py` decides that).

Per row: effective dimensions B'/L' come from that row's own eccentricities `ex_m`/`ey_m`
(`RigaVerifica`, already the resultant's eccentricity at the base); the horizontal load H and its
direction θ (relative to the L' axis, EN 1997-1 Annex D.2 `esponente_m`) come from that row's own
base shears `vx_kN`/`vy_kN`; the embedment is the tool's `h_interro_m` input, the same for every
row. `verifica_drenata`/`verifica_non_drenata` are always called with `sismico=False`: the shared
module has no seismic bearing-capacity formula of its own (Paolucci-Pecker, "Da confermare"), so a
seismic row uses the identical static formula, and `capacita_portante.py` adds a warning instead
[A] (docs/architecture-phase4.md §C, "Design: ... seismic: γR = 2.3 with ... advanced, default off,
flagged 'Da confermare'")."""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.capacita_portante import Condizione, verifica_drenata, verifica_non_drenata
from strutture.shared.load_table import Famiglia
from strutture.shared.report import CalcError

from .riga_verifica import RigaVerifica


class RigaCapacitaPortante(BaseModel):
    """Bearing-capacity check of one `reazioni` row (key columns echoed for the `righe` result)."""

    model_config = ConfigDict(frozen=True)

    nodo: int = Field(description="Nodo della struttura", json_schema_extra={"unit": "-"})
    combo: str = Field(description="Nome della combinazione di carico", json_schema_extra={"unit": "-"})
    famiglia: Famiglia = Field(description="Famiglia della combinazione", json_schema_extra={"unit": "-"})
    q_lim_kpa: float = Field(description="Pressione limite di capacità portante q_lim (EN 1997-1 Annesso D)",
                              ge=0, json_schema_extra={"unit": "kPa", "symbol": "q_lim"})
    r_d_kn: float = Field(description="Resistenza di progetto R_d = q_lim·A' / γR",
                           ge=0, json_schema_extra={"unit": "kN", "symbol": "R_d"})
    n_ed_kn: float = Field(description="Azione verticale di progetto N_Ed alla base",
                            ge=0, json_schema_extra={"unit": "kN", "symbol": "N_Ed"})
    ratio: float = Field(description="Grado di sfruttamento della capacità portante N_Ed / R_d",
                          ge=0, json_schema_extra={"unit": "-", "symbol": "N_Ed/R_d"})
    b_eff_m: float = Field(description="Larghezza efficace della base B' per questa combinazione",
                            gt=0, json_schema_extra={"unit": "m", "symbol": "B'"})
    l_eff_m: float = Field(description="Lunghezza efficace della base L' per questa combinazione",
                            gt=0, json_schema_extra={"unit": "m", "symbol": "L'"})


def capacita_portante_riga(
    riga: RigaVerifica, *, ax_m: float, by_m: float, profondita_piano_posa_m: float,
    condizione: Condizione, phi_k_deg: float | None, c_k_kpa: float | None, cu_k_kpa: float | None,
    gamma_kn_m3: float, profondita_falda_m: float | None,
) -> RigaCapacitaPortante:
    """Bearing-capacity check of `riga`, per docs/architecture-phase4.md §C. Raises `CalcError`
    (naming the combo/nodo) for geometry/equilibrium the shared module cannot verify (eccentricity
    outside the footing, horizontal load exceeding the available friction/adhesion)."""
    h_kn = math.hypot(riga.vx_kN, riga.vy_kN)
    theta_deg = math.degrees(math.atan2(riga.vx_kN, riga.vy_kN)) if h_kn > 0 else 0.0
    try:
        if condizione == "drenata":
            if phi_k_deg is None or c_k_kpa is None:
                raise ValueError("phi_k_deg e c_k_kpa sono obbligatori in condizione drenata")
            verifica = verifica_drenata(
                n_ed_kn=riga.n_kN, b_m=ax_m, l_m=by_m, eb_m=riga.ex_m, el_m=riga.ey_m,
                phi_k_deg=phi_k_deg, c_k_kpa=c_k_kpa, gamma_kn_m3=gamma_kn_m3,
                profondita_piano_posa_m=profondita_piano_posa_m, profondita_falda_m=profondita_falda_m,
                h_kn=h_kn, direzione_h="theta", theta_deg=theta_deg,
            )
        else:
            if cu_k_kpa is None:
                raise ValueError("cu_k_kpa è obbligatorio in condizione non drenata")
            verifica = verifica_non_drenata(
                n_ed_kn=riga.n_kN, b_m=ax_m, l_m=by_m, eb_m=riga.ex_m, el_m=riga.ey_m,
                cu_k_kpa=cu_k_kpa, gamma_kn_m3=gamma_kn_m3,
                profondita_piano_posa_m=profondita_piano_posa_m, h_kn=h_kn,
            )
    except CalcError as error:
        raise CalcError(f"combinazione '{riga.combo}' (nodo {riga.nodo}): {error}") from error
    area = verifica.carico_limite.area_efficace
    return RigaCapacitaPortante(
        nodo=riga.nodo, combo=riga.combo, famiglia=riga.famiglia,
        q_lim_kpa=verifica.carico_limite.q_lim_kpa, r_d_kn=verifica.r_d_kn, n_ed_kn=verifica.n_ed_kn,
        ratio=verifica.ratio, b_eff_m=area.b_eff_m, l_eff_m=area.l_eff_m,
    )

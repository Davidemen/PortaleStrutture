"""Step: composes the optional NTC2018 §6.4.2.1 bearing-capacity check over every `reazioni` row
(docs/architecture-phase4.md §C "Integration"): empty when the input "Terreno" block is not filled
(`terreno_condizione` absent, the tool's typed `resistenze` stays the only bearing signal, unchanged
from before this feature); one `RigaCapacitaPortante` per ULS `righe` row (SLU_*/SLV_*; SLE_* rows
are a serviceability check, not part of NTC2018 §6.4.2.1 and never compared to R_d here), plus the
per-famiglia envelope and the single overall governing row (worst N_Ed/R_d), when it is.

The founding plane is `h_interro_m` (soil cover ABOVE the slab, `pesi_propri.py`'s convention)
PLUS `h_plinto_m` (the slab's own height): `pesi_propri.w_terreno_kN` only ever multiplies
`h_interro_m` by the plan area net of the pedestal, i.e. `h_interro_m` alone is the depth to the
TOP of the slab, not to the founding plane at its bottom. `h_pedestal_sotto_m` (the part of the
pedestal below ground level, per `models.py`) sits ABOVE the slab in every drawing (`schizzo.py`'s
`_sezione`: the pedestal rectangle starts at `y=h_plinto_m`, on top of the slab, never below it),
so it never changes how deep the slab's own base sits and is correctly left out of this sum.

`legacy_compat=True` ignores the block with a warning: the original spreadsheet has no bearing-
capacity calculation at all (`plinti-isolati/capacita-portante-terreno-assente-nel-foglio`,
src/strutture/data/divergences/plinti-isolati.json)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.divergences import legacy
from strutture.shared.load_table import EnvelopeRow, envelope, governing

from .capacita_portante_riga import RigaCapacitaPortante, capacita_portante_riga
from .input import PlintoIsolatoInput
from .riga_verifica import RigaVerifica

AVVISO_BLOCCO_IGNORATO_LEGACY = (
    "Blocco 'Terreno' ignorato in modalità legacy: il foglio Excel originale non esegue alcuna "
    "verifica di capacità portante NTC2018 §6.4.2.1."
)
FAMIGLIE_SISMICHE: tuple[str, ...] = ("SLV_STR", "SLV_EQU")
# SLU_*/SLV_* only: SLE_* (esercizio) rows have no NTC2018 §6.4.2.1 bearing-capacity meaning (that
# clause is an ultimate-limit-state check, R_d = q_lim*A'/gammaR) and must never enter `righe`,
# `inviluppo` or `governante` (MEDIUM finding: an SLE row could otherwise silently become the
# governing row under the ULS Check in `capacita_portante_checks.py`).
FAMIGLIE_SLU: tuple[str, ...] = ("SLU_STR", "SLU_EQU", *FAMIGLIE_SISMICHE)
AVVISO_SISMICO = "Verifica di portanza in condizioni sismiche: coefficienti da confermare con il progettista"


class CapacitaPortanteOutput(BaseModel):
    """Bearing-capacity check per `reazioni` row, envelope and governing row; every field is empty
    when the "Terreno" block is not filled (or is ignored under `legacy_compat=True`)."""

    model_config = ConfigDict(frozen=True)

    righe: tuple[RigaCapacitaPortante, ...] = Field(
        default=(),
        description="Capacità portante NTC2018 §6.4.2.1 di ogni combinazione (blocco Terreno compilato)",
        json_schema_extra={"rows_page": 200},
    )
    inviluppo: tuple[EnvelopeRow, ...] = Field(
        default=(), description="Grado di sfruttamento N_Ed/R_d governante per famiglia")
    governante: RigaCapacitaPortante | None = Field(
        default=None, description="Combinazione governante per il grado di sfruttamento N_Ed/R_d")


def capacita_portante(righe: tuple[RigaVerifica, ...], inputs: PlintoIsolatoInput) -> tuple[CapacitaPortanteOutput, tuple[str, ...]]:
    """`(CapacitaPortanteOutput(), ())` when the block is empty; ignores it with a warning under
    `legacy_compat=True`; otherwise one `RigaCapacitaPortante` per ULS (`FAMIGLIE_SLU`) `righe`
    row, with an added warning when any seismic family (SLV_*) is present."""
    if inputs.terreno_condizione is None:
        return CapacitaPortanteOutput(), ()
    if legacy("plinti-isolati/capacita-portante-terreno-assente-nel-foglio", inputs.legacy_compat):
        return CapacitaPortanteOutput(), (AVVISO_BLOCCO_IGNORATO_LEGACY,)
    righe_capacita = tuple(
        capacita_portante_riga(
            riga, ax_m=inputs.ax_m, by_m=inputs.by_m,
            profondita_piano_posa_m=inputs.h_interro_m + inputs.h_plinto_m,
            condizione=inputs.terreno_condizione, phi_k_deg=inputs.terreno_phi_k_deg,
            c_k_kpa=inputs.terreno_c_k_kpa, cu_k_kpa=inputs.terreno_cu_k_kpa,
            gamma_kn_m3=inputs.terreno_gamma_kn_m3, profondita_falda_m=inputs.terreno_profondita_falda_m,
        )
        for riga in righe if riga.famiglia in FAMIGLIE_SLU
    )
    inviluppo_righe = envelope(righe_capacita, lambda r: r.ratio, "max", by="famiglia")  # type: ignore[arg-type]
    governante_env = governing(righe_capacita, lambda r: r.ratio, "max")  # type: ignore[arg-type]
    governante = righe_capacita[governante_env.indice] if governante_env is not None else None
    avvisi = (AVVISO_SISMICO,) if any(r.famiglia in FAMIGLIE_SISMICHE for r in righe_capacita) else ()
    return CapacitaPortanteOutput(righe=righe_capacita, inviluppo=inviluppo_righe, governante=governante), avvisi

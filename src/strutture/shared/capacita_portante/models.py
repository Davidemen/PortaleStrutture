"""Frozen result models for EN 1997-1 Annex D bearing capacity (docs/architecture-phase4.md §C).

SI-engineering units throughout (kPa, kN, kN/m³, m, degrees) — matches the convention of the
other `shared/*` physics modules (e.g. `shared/footing_pressure/models.py`).
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Condizione = Literal["drenata", "non_drenata"]
Direzione = Literal["B", "L", "theta"]  # direction of the horizontal load H relative to the footing axes


class FattoriPortanza(BaseModel):
    """Nq, Nc, Nγ (EN 1997-1 Annex D.4, rough base)."""

    model_config = ConfigDict(frozen=True)

    nq: float = Field(description="Fattore di capacità portante Nq", gt=0)
    nc: float = Field(description="Fattore di capacità portante Nc", gt=0)
    ngamma: float = Field(description="Fattore di capacità portante Nγ (base scabra)", ge=0)


class FattoriForma(BaseModel):
    """sq, sγ, sc (EN 1997-1 Annex D.2/D.3, rectangular footing B' x L')."""

    model_config = ConfigDict(frozen=True)

    sq: float = Field(description="Fattore di forma sq", gt=0)
    sgamma: float = Field(description="Fattore di forma sγ", gt=0)
    sc: float = Field(description="Fattore di forma sc", gt=0)


class FattoriInclinazioneCarico(BaseModel):
    """iq, iγ, ic and the exponent m used to compute iq/iγ (EN 1997-1 Annex D.2/D.3)."""

    model_config = ConfigDict(frozen=True)

    m: float = Field(description="Esponente m in funzione della direzione del carico orizzontale", gt=0)
    iq: float = Field(description="Fattore di inclinazione del carico iq", ge=0, le=1)
    igamma: float = Field(description="Fattore di inclinazione del carico iγ", ge=0, le=1)
    ic: float = Field(description="Fattore di inclinazione del carico ic", ge=0, le=1)


class FattoriInclinazioneBase(BaseModel):
    """bq, bγ, bc (EN 1997-1 Annex D.2/D.3, base inclined at α to the horizontal)."""

    model_config = ConfigDict(frozen=True)

    bq: float = Field(description="Fattore di inclinazione della base bq", ge=0, le=1)
    bgamma: float = Field(description="Fattore di inclinazione della base bγ", ge=0, le=1)
    bc: float = Field(description="Fattore di inclinazione della base bc", ge=0, le=1)


class AreaEfficace(BaseModel):
    """Effective (Meyerhof) area B' x L' of an eccentrically loaded rectangular footing."""

    model_config = ConfigDict(frozen=True)

    b_eff_m: float = Field(description="Larghezza efficace B' (lato corto, B' <= L')", gt=0)
    l_eff_m: float = Field(description="Lunghezza efficace L' (lato lungo; infinita per una base nastriforme)", gt=0)
    a_eff_m2: float = Field(description="Area efficace A' (per metro di sviluppo se nastriforme)", gt=0)
    nastriforme: bool = Field(description="True per una base nastriforme (L' -> infinito, fattori di forma = 1)")
    scambiato: bool = Field(
        description="True se i lati B/L fisici sono stati scambiati per ottenere b_eff_m<=l_eff_m "
        "(b_eff_m contiene allora la quantita' calcolata lungo l'asse fisico L, e viceversa)")


class CaricoLimiteResult(BaseModel):
    """Ultimate bearing pressure q_lim with every intermediate factor reported."""

    model_config = ConfigDict(frozen=True)

    condizione: Condizione = Field(description="Condizione di carico: drenata o non drenata")
    q_lim_kpa: float = Field(description="Pressione limite di capacità portante q_lim", ge=0)
    area_efficace: AreaEfficace = Field(description="Area efficace B' x L' usata nel calcolo")
    fattori_portanza: FattoriPortanza | None = Field(
        default=None, description="Nq, Nc, Nγ (solo condizione drenata)")
    fattori_forma: FattoriForma = Field(description="Fattori di forma sq, sγ, sc")
    fattori_inclinazione_carico: FattoriInclinazioneCarico = Field(
        description="Fattori di inclinazione del carico iq, iγ, ic (m, igamma=iq=1 in condizione non drenata)")
    fattori_inclinazione_base: FattoriInclinazioneBase = Field(description="Fattori di inclinazione della base bq, bγ, bc")
    q_eff_kpa: float = Field(description="Sovraccarico efficace q' al piano di posa", ge=0)
    gamma_eff_kn_m3: float | None = Field(
        default=None, description="Peso di volume efficace γ' usato nel termine di Nγ (solo condizione drenata)")
    avviso_fattori_profondita: str | None = Field(
        default=None, description="Avviso se sono stati applicati i fattori di profondità di Hansen (non previsti da EN 1997-1 Annex D)")


class VerificaCapacitaPortante(BaseModel):
    """NTC 2018 §6.4.2.1 approccio 2 (A1+M1+R3) bearing capacity check."""

    model_config = ConfigDict(frozen=True)

    carico_limite: CaricoLimiteResult = Field(description="Dettaglio del calcolo di q_lim")
    r_d_kn: float = Field(description="Resistenza di progetto R_d = q_lim * A' / γR", ge=0)
    n_ed_kn: float = Field(description="Azione verticale di progetto N_Ed", ge=0)
    ratio: float = Field(description="Grado di sfruttamento N_Ed / R_d", ge=0)
    passed: bool = Field(description="True se N_Ed <= R_d")

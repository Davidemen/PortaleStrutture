"""Frozen pydantic models for the office settings (WORKBENCH_SPEC.md §26.2)."""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TipoDato = Literal[
    "lunghezza_m", "lunghezza_cm", "lunghezza_mm", "diametro_armatura", "passo_armatura", "copriferro",
    "spessore", "intero",
]
TIPI_DATO: tuple[TipoDato, ...] = (
    "lunghezza_m", "lunghezza_cm", "lunghezza_mm", "diametro_armatura", "passo_armatura", "copriferro",
    "spessore", "intero",
)
MAX_ECCEZIONI = 200
PASSO_MAX = 1000.0
_DECIMALI_OBIETTIVO = 2
_DECIMALI_PASSO = 4
_MAX_SIGLA = 12


def _decimali(valore: float) -> int:
    """Number of decimal digits of `valore` on its own decimal string (no binary-float drift)."""
    testo = format(Decimal(str(valore)).normalize(), "f")
    return len(testo.split(".", 1)[1]) if "." in testo else 0


class PassoCampo(BaseModel):
    """One office exception: the rounding step for a single (strumento, campo) pair.

    `passo = None` means "no step for this field" and masks the type step (§26.5)."""

    model_config = ConfigDict(frozen=True)

    strumento: str = Field(min_length=1, max_length=80)
    campo: str = Field(min_length=1, max_length=120)
    passo: float | None = Field(default=None, gt=0, le=PASSO_MAX)

    @field_validator("passo")
    @classmethod
    def _al_massimo_4_decimali(cls, valore: float | None) -> float | None:
        if valore is not None and _decimali(valore) > _DECIMALI_PASSO:
            raise ValueError(f"il passo deve avere al massimo {_DECIMALI_PASSO} decimali")
        return valore


class Impostazioni(BaseModel):
    """The office defaults. `FABBRICA` below is the single definition of the factory values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    obiettivo_sfruttamento: float = Field(default=1.0, gt=0, le=1.0)
    obiettivo_su_verifiche_minimo: bool = False
    passi_per_tipo: dict[TipoDato, float | None] = Field(default_factory=lambda: dict.fromkeys(TIPI_DATO))
    passi_per_campo: tuple[PassoCampo, ...] = ()

    @field_validator("obiettivo_sfruttamento")
    @classmethod
    def _obiettivo_valido(cls, valore: float) -> float:
        if _decimali(valore) > _DECIMALI_OBIETTIVO:
            raise ValueError(
                f"L'obiettivo di sfruttamento deve avere al massimo {_DECIMALI_OBIETTIVO} decimali"
            )
        return valore

    @field_validator("passi_per_tipo")
    @classmethod
    def _passi_per_tipo_validi(cls, valore: dict[TipoDato, float | None]) -> dict[TipoDato, float | None]:
        completo = {**dict.fromkeys(TIPI_DATO), **valore}
        for tipo, passo in completo.items():
            _valida_passo_tipo(tipo, passo)
        return completo

    @model_validator(mode="after")
    def _eccezioni_valide(self) -> "Impostazioni":
        if len(self.passi_per_campo) > MAX_ECCEZIONI:
            raise ValueError(f"al massimo {MAX_ECCEZIONI} eccezioni per campo")
        visti: set[tuple[str, str]] = set()
        for eccezione in self.passi_per_campo:
            chiave = (eccezione.strumento, eccezione.campo)
            if chiave in visti:
                raise ValueError(f"eccezione duplicata per {eccezione.strumento}.{eccezione.campo}")
            visti.add(chiave)
        return self


def _valida_passo_tipo(tipo: TipoDato, passo: float | None) -> None:
    if passo is None:
        return
    if not (0 < passo <= PASSO_MAX):
        raise ValueError(f"il passo di {tipo} deve essere maggiore di 0 e al massimo {PASSO_MAX}")
    if _decimali(passo) > _DECIMALI_PASSO:
        raise ValueError(f"il passo di {tipo} deve avere al massimo {_DECIMALI_PASSO} decimali")
    if tipo == "intero" and (passo != int(passo) or passo < 1):
        raise ValueError("Il passo deve essere intero")


FABBRICA = Impostazioni()


class ImpostazioniSalvate(BaseModel):
    """`Impostazioni` plus the storage bookkeeping (revisione 0 = never saved, factory values)."""

    model_config = ConfigDict(frozen=True)

    valori: Impostazioni = FABBRICA
    revisione: int = 0
    sigla: str = Field(default="", max_length=_MAX_SIGLA)
    aggiornato_il: str = ""

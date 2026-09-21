"""The divergence register: every place where the default (code-standard) result differs from the
original spreadsheet. Source of truth = `src/strutture/data/divergences/<unita>.json`; the markdown
under docs/divergences/ is generated from it."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Tipo = Literal["errore_foglio", "aggiornamento_normativo", "scelta_ingegneristica", "da_verificare"]
Ramo = Literal["codice", "condiviso", "nessuno"]
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*$")  # "<unita>/<slug>"


class Divergence(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description='Stable key "<unita>/<slug>", e.g. "ca-pilastri/lambda-lim-unita"; never reused')
    titolo: str = Field(min_length=5, max_length=120, description="One Italian sentence an engineer recognises")
    tipo: Tipo
    strumenti: tuple[str, ...] = Field(description="Tool names affected (empty for shared modules used indirectly)")
    cella: str = Field(default="", description="Sheet!cell(s) where the spreadsheet does it, if any")
    foglio: str = Field(min_length=3, description="What the spreadsheet does (Italian)")
    corretto: str = Field(min_length=3, description="What the default mode does instead (Italian)")
    clausola: str = Field(default="", description="Governing clause, e.g. 'NTC2018 §4.1.2.3.9.2'")
    impatto: str = Field(default="", description="Numeric impact on the golden case, e.g. 'λ_lim 1084 -> 34,3'")
    uscite: tuple[str, ...] = Field(default=(), description="Output paths that can change, e.g. 'snellezza.lambda_lim'")
    ramo: Ramo = Field(default="codice", description=(
        'How Excel mode relates to this entry. "codice": a `legacy("<id>", legacy_compat)` branch reproduces the '
        'spreadsheet. "condiviso": Excel mode DOES reproduce it, but through another entry\'s branch (`riprodotta_da`) '
        'or a per-norm rules table, not through a call of its own. "nessuno": Excel mode does NOT reproduce it '
        "(a fix applied in both modes, a sheet label or limit, an input-schema change)"))
    motivo_senza_ramo: str = Field(default="", description='Why there is no own branch (Italian); required iff ramo != "codice"')
    riprodotta_da: tuple[str, ...] = Field(default=(), description='ramo="condiviso" only: ids of the entries whose branch reproduces this one')

    @field_validator("id")
    @classmethod
    def _id_format(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"id {value!r} must look like '<unita>/<slug>' (lowercase, digits, hyphens)")
        return value

    @model_validator(mode="after")
    def _ramo_coerente(self) -> "Divergence":
        if self.ramo != "codice" and len(self.motivo_senza_ramo.strip()) < 5:
            raise ValueError(f'ramo="{self.ramo}" requires motivo_senza_ramo (why there is no legacy branch of its own)')
        if self.ramo == "codice" and self.motivo_senza_ramo:
            raise ValueError('motivo_senza_ramo is only allowed when ramo is not "codice"')
        if self.riprodotta_da and self.ramo != "condiviso":
            raise ValueError('riprodotta_da is only allowed with ramo="condiviso"')
        return self

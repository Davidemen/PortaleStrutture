"""Flat input model for `fond-pavimento-industriale` (BUILD_CONTRACT: inputs stay flat except the
`carichi` table field, architecture-batch2.md §2). Fields follow the sheet's top-to-bottom column
order: `B:D` materials/geometry, `F:I` distributed load, `K:O`/`Q:U` concentrated loads (now the
`carichi` table), then the joint prescriptions further down column `C`/`G`/`H`."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.tabular import table_field

from .carico_row import CaricoRow
from .materiali import ClasseCalcestruzzoPavimento
from .tables import SottofondoTipo

MAX_CARICHI_ROWS = 12
COEFF_VRD_MAX_DESCRIPTION = (
    "Coefficiente di vRd,max = c·ν·fcd: 0,4 (EN 1992-1-1/A1:2014, consigliato) oppure 0,5 "
    "(EN 1992-1-1:2004 con Appendice Nazionale italiana)"
)


class PavimentoIndustrialeInput(BaseModel):
    """`carichi_distribuiti_concentrati` — CNR-DT 211/2014 industrial ground slab checks."""

    model_config = ConfigDict(frozen=True)

    classe_calcestruzzo: ClasseCalcestruzzoPavimento = Field(description="Classe di resistenza del calcestruzzo (C4)", json_schema_extra={"group": "Materiali"})
    gamma_c: float = Field(default=1.5, description="Coefficiente parziale del calcestruzzo γc (C7)", gt=1, le=2, json_schema_extra={"symbol": "γ_c", "group": "Materiali", "advanced": True})
    gamma_s: float = Field(default=1.15, description="Coefficiente parziale dell'acciaio γs (C20)", gt=1, le=2, json_schema_extra={"symbol": "γ_s", "group": "Materiali", "advanced": True})
    nu_poisson: float = Field(default=0.2, description="Coefficiente di Poisson del calcestruzzo ν (C15)", gt=0, lt=0.5, json_schema_extra={"symbol": "ν", "group": "Materiali", "advanced": True})

    sottofondo_tipo: SottofondoTipo | None = Field(
        default=None, description="Tipo di sottofondo, per la stima automatica di kT (C24, tabella Winkler)",
        json_schema_extra={"group": "Sottofondo"},
    )
    kt_manuale_N_mm3: float | None = Field(
        default=None, description="Modulo di reazione del sottofondo kT, in alternativa a 'Tipo di sottofondo'",
        gt=0, json_schema_extra={"unit": "N/mm3", "symbol": "k_T", "group": "Sottofondo", "advanced": True},
    )
    h_mm: float = Field(description="Spessore della piastra h (C27)", gt=50, le=1000, json_schema_extra={"unit": "mm", "symbol": "h", "group": "Sottofondo"})
    c_mm: float = Field(description="Copriferro c (C28)", gt=0, le=100, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Sottofondo"})

    phi_rete_mm: float = Field(description="Diametro della rete elettrosaldata φ (G31/H31, L44/N44)", gt=0, le=30, json_schema_extra={"unit": "mm", "symbol": "φ", "group": "Armatura"})
    passo_rete_mm: float = Field(description="Passo della rete elettrosaldata S (G32/H32, L45/N45)", gt=0, le=500, json_schema_extra={"unit": "mm", "symbol": "S", "group": "Armatura"})

    g_daN_m2: float = Field(default=0.0, description="Carico permanente distribuito G (G4)", ge=0, json_schema_extra={"unit": "daN/m2", "symbol": "G", "group": "Carico distribuito"})
    gamma_g: float = Field(default=1.3, description="Coefficiente parziale permanente γG (G5)", gt=0, le=2, json_schema_extra={"symbol": "γ_G", "group": "Carico distribuito", "advanced": True})
    q_daN_m2: float = Field(description="Carico variabile distribuito Q (G6)", ge=0, json_schema_extra={"unit": "daN/m2", "symbol": "Q", "group": "Carico distribuito"})
    gamma_q: float = Field(default=1.5, description="Coefficiente parziale variabile γQ (G7)", gt=0, le=2, json_schema_extra={"symbol": "γ_Q", "group": "Carico distribuito", "advanced": True})
    psi1_distribuito: float = Field(default=0.9, description="Coefficiente di combinazione frequente ψ1 (G8)", gt=0, le=1, json_schema_extra={"symbol": "ψ_1", "group": "Carico distribuito", "advanced": True})

    carichi: tuple[CaricoRow, ...] = table_field(
        CaricoRow, max_rows=MAX_CARICHI_ROWS, key="caso",
        description="Carichi concentrati (ruote/impronte) per caso e posizione (K:O, Q:U)",
    )

    a_contrazione_m: float = Field(description="Dimensione a' del pannello di contrazione (C39)", gt=0, le=100, json_schema_extra={"unit": "m", "symbol": "a'", "group": "Giunti"})
    b_contrazione_m: float = Field(description="Dimensione b' del pannello di contrazione (C40)", gt=0, le=100, json_schema_extra={"unit": "m", "symbol": "b'", "group": "Giunti"})
    a_isolamento_m: float = Field(description="Dimensione a del pannello di isolamento (C41)", gt=0, le=100, json_schema_extra={"unit": "m", "symbol": "a", "group": "Giunti"})
    b_isolamento_m: float = Field(description="Dimensione b del pannello di isolamento (C42)", gt=0, le=100, json_schema_extra={"unit": "m", "symbol": "b", "group": "Giunti"})
    alpha_termico: float = Field(default=1e-5, description="Coefficiente di dilatazione termica α (C43)", gt=0, le=1e-3, json_schema_extra={"unit": "1/°C", "symbol": "α", "group": "Giunti", "advanced": True})
    delta_t_C: float = Field(description="Escursione termica di progetto ΔT (C44)", gt=0, le=100, json_schema_extra={"unit": "°C", "symbol": "ΔT", "group": "Giunti"})

    coeff_vrd_max: Literal[0.4, 0.5] = Field(
        default=V_RD_MAX_COEFF_A1_2014, description=COEFF_VRD_MAX_DESCRIPTION,
        json_schema_extra={"symbol": "c", "group": "Avanzate", "advanced": True},
    )
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _sottofondo_esattamente_uno(self) -> "PavimentoIndustrialeInput":
        if (self.sottofondo_tipo is None) == (self.kt_manuale_N_mm3 is None):
            raise ValueError("indicare esattamente uno tra 'Tipo di sottofondo' e 'kT manuale'")
        return self

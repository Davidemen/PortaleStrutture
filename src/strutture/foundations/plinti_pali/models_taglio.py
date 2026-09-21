"""Result models for the shear/punching design step (see `taglio_punzonamento.py`)."""
from pydantic import BaseModel, ConfigDict, Field


class Taglio(BaseModel):
    """Beam shear at the reduced distance `av` from the pile face (EC2 §6.2.2(6))."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile", gt=0, json_schema_extra={"unit": "mm"})
    ved_kN: float = Field(description="Taglio sollecitante VEd", ge=0, json_schema_extra={"unit": "kN"})
    ved_ridotto_kN: float = Field(description="Taglio ridotto VEd' (av < 2d)", ge=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed'"})
    k: float = Field(description="Fattore dimensionale k", gt=0, json_schema_extra={"unit": "-"})
    rho: float = Field(description="Rapporto geometrico di armatura longitudinale", ge=0, json_schema_extra={"unit": "-", "symbol": "ρ"})
    vrd_c_MPa: float = Field(description="Tensione resistente a taglio del calcestruzzo", ge=0, json_schema_extra={"unit": "N/mm2"})
    vrd_c_kN: float = Field(description="Resistenza a taglio VRd,c", ge=0, json_schema_extra={"unit": "kN"})
    ved_max_kN: float = Field(
        description="Taglio massimo ammissibile al filo (schiacciamento del puntone), VEd <= 0.5*b*d*ν*fcd",
        ge=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed,max"},
    )
    utilizzo: float = Field(description="VEd' / VRd,c", ge=0, json_schema_extra={"unit": "-"})
    verificato: bool = Field(description="VEd' <= VRd,c (e, in modalità normale, VEd <= VEd,max, EC2 eq. 6.5)")


class Punzonamento(BaseModel):
    """Column-face punching (EC2 §6.4.5, checked at the column perimeter, no offset)."""

    model_config = ConfigDict(frozen=True)

    u_mm: float = Field(description="Perimetro di verifica al filo pilastro", gt=0, json_schema_extra={"unit": "mm"})
    beta: float = Field(
        description="Coefficiente di eccentricità β (EC2 §6.4.3, eq. 6.39 semplificata; 1.0 = nessuna eccentricità o modalità legacy)",
        ge=1.0, json_schema_extra={"unit": "-", "symbol": "β"},
    )
    ved_kN: float = Field(description="Taglio di punzonamento sollecitante VEd = β*NSd", ge=0, json_schema_extra={"unit": "kN"})
    vrd_max_kN: float = Field(description="Resistenza massima a punzonamento VRd,max", ge=0, json_schema_extra={"unit": "kN"})
    utilizzo: float = Field(description="VEd / VRd,max", ge=0, json_schema_extra={"unit": "-"})
    verificato: bool = Field(description="VEd <= VRd,max")
    interasse_x_sufficiente: bool = Field(description="Interasse pali in X sufficiente a non sovrapporre i coni di punzonamento")
    interasse_y_sufficiente: bool = Field(description="Interasse pali in Y sufficiente a non sovrapporre i coni di punzonamento")


class PunzonamentoPalo(BaseModel):
    """Punching of the corner (governing) pile, at its own control perimeter 2d from the pile face
    (EC2 §6.4.2) — an addition beyond the source sheet, which only gates on pile spacing."""

    model_config = ConfigDict(frozen=True)

    u_mm: float = Field(description="Perimetro di verifica (ridotto per sovrapposizione con pali/bordi adiacenti in modalità normale)",
                         gt=0, json_schema_extra={"unit": "mm"})
    a_mm: float = Field(
        description="Distanza dal filo palo effettivamente disponibile prima di bordo plinto o palo adiacente (<= 2d)",
        gt=0, json_schema_extra={"unit": "mm", "symbol": "a"},
    )
    ved_kN: float = Field(description="Reazione assiale massima sul palo", ge=0, json_schema_extra={"unit": "kN"})
    vrd_c_kN: float = Field(description="Resistenza a punzonamento del calcestruzzo VRd,c", ge=0, json_schema_extra={"unit": "kN"})
    utilizzo: float = Field(description="Ved / VRd,c", ge=0, json_schema_extra={"unit": "-"})
    verificato: bool = Field(description="Ved <= VRd,c")


class CapacitaPalo(BaseModel):
    """Pile axial capacity check against the user-given geotechnical/structural pile resistance."""

    model_config = ConfigDict(frozen=True)

    domanda_kN: float = Field(description="Reazione di progetto sul palo", json_schema_extra={"unit": "kN"})
    resistenza_kN: float = Field(description="Resistenza ammissibile del palo", gt=0, json_schema_extra={"unit": "kN"})
    utilizzo: float = Field(description="Domanda / resistenza", ge=0, json_schema_extra={"unit": "-"})
    verificato: bool = Field(description="Domanda <= resistenza")

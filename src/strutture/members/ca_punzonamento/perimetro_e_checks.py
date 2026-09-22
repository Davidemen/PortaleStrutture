"""Composizione del perimetro critico e delle verifiche di base per `compose.run`: estratte in
modulo a parte per restare entro i 150 righe per modulo (regola dura 12)."""
from strutture.shared.divergences import legacy
from strutture.shared.report import Check

from . import governing_capacity as gov
from .models import PerimetroCriticoOutput, PunzonamentoInput
from .perimeter_scan import scan_perimetro
from .reinforcement_ratio import RHO_MAX_WARNING

RHO_L_CLAUSE = "EN 1992-1-1 §6.4.4(1)"
FACCIA_CLAUSE = "EN 1992-1-1 §6.4.5(3)"
PERIMETRO_CLAUSE = "EN 1992-1-1 §6.4.4"


def perimetro_critico(
    inputs: PunzonamentoInput, beta: float, d_mm: float, k: float, rho: float
) -> tuple[PerimetroCriticoOutput, gov.GoverningCapacity]:
    righe, governing = scan_perimetro(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, d_mm, k, rho, inputs.fck_MPa, legacy_compat=inputs.legacy_compat,
    )
    capacity = gov.governing_capacity(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, inputs.a_amanuale_mm2, governing.x, d_mm, k, rho, inputs.fck_MPa,
        legacy_compat=inputs.legacy_compat,
    )
    perimetro_critico_output = PerimetroCriticoOutput(
        righe=righe, a_governante_su_d=governing.x, a_governante_mm=capacity.a_governante_mm, ui_mm=capacity.ui_mm,
        area_mm2=capacity.area_mm2, rho=rho, k=k, ved_red_ui_kN=capacity.ved_red_ui_kN, v_rd_i_MPa=capacity.v_rd_i_MPa,
        v_ed_i_MPa=capacity.v_ed_i_MPa, rapporto=capacity.rapporto, armatura_necessaria=capacity.armatura_necessaria,
    )
    return perimetro_critico_output, capacity


def checks_base(
    inputs: PunzonamentoInput, faccia, capacity: gov.GoverningCapacity, rho: float
) -> tuple[Check, ...]:
    # Stesso id di column_face.v_rd_max_MPa: la nota informativa "coeff scelto in input" ha senso
    # solo in modalità codice, dove coeff_vrd_max è davvero usato (in modalità foglio vRd,max usa
    # il coefficiente semplificato cablato, non l'input).
    faccia_detail = (
        ""
        if legacy("ca-punzonamento/vrd-max-filo-pilastro-coefficiente-semplificato", inputs.legacy_compat)
        else f"vRd,max = {inputs.coeff_vrd_max:g}·ν·fcd (c scelto in input)"
    )
    return (
        Check(name="Punzonamento al filo del pilastro", passed=faccia.v_ed_0_MPa < faccia.v_rd_max_MPa, clause=FACCIA_CLAUSE,
              detail=faccia_detail, value=faccia.v_ed_0_MPa, limit=faccia.v_rd_max_MPa, unit="MPa"),
        Check(name="Punzonamento al perimetro critico", passed=not capacity.armatura_necessaria, clause=PERIMETRO_CLAUSE,
              value=capacity.v_ed_i_MPa, limit=capacity.v_rd_i_MPa, unit="MPa"),
        Check(name="Percentuale massima di armatura tesa", passed=rho <= RHO_MAX_WARNING, clause=RHO_L_CLAUSE, value=rho, limit=RHO_MAX_WARNING, unit="-"),
    )

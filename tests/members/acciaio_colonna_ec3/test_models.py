"""ColonnaEc3Input — validation at system boundaries (BUILD_CONTRACT: bounds, Literal enums)."""
import pytest
from pydantic import ValidationError

from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.tool import ESEMPIO_AUREO


@pytest.mark.unit
def test_valid_golden_input_round_trips() -> None:
    inputs = ColonnaEc3Input(**ESEMPIO_AUREO)
    assert inputs.b_mm == 280
    assert inputs.grado_acciaio == "Q345"


@pytest.mark.unit
def test_frozen_model_rejects_mutation() -> None:
    inputs = ColonnaEc3Input(**ESEMPIO_AUREO)
    with pytest.raises(ValidationError):
        inputs.b_mm = 999  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.parametrize("campo,valore", [("b_mm", 0), ("h_mm", -1), ("tw_mm", 0), ("area_mm2", -10)])
def test_non_positive_geometry_rejected(campo: str, valore: float) -> None:
    dati = {**ESEMPIO_AUREO, campo: valore}
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**dati)


@pytest.mark.unit
def test_unknown_steel_grade_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "grado_acciaio": "S460"})


@pytest.mark.unit
def test_unknown_diagram_type_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "diagramma_tipo_y": "4"})


@pytest.mark.unit
def test_unknown_classe_sezione_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "classe_sezione": "classe 3"})


@pytest.mark.unit
def test_gamma_out_of_bounds_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "gamma_m0": 3.0})


@pytest.mark.unit
def test_gamma_none_is_allowed() -> None:
    inputs = ColonnaEc3Input(**{**ESEMPIO_AUREO, "gamma_m0": None, "gamma_m1": None})
    assert inputs.gamma_m0 is None
    assert inputs.gamma_m1 is None


@pytest.mark.unit
def test_negative_shear_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "vy_sd_kN": -1.0})


@pytest.mark.unit
def test_negative_axial_rejected() -> None:
    with pytest.raises(ValidationError):
        ColonnaEc3Input(**{**ESEMPIO_AUREO, "nsd_kN": -1.0})

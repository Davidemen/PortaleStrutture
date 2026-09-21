"""Sketch primitives: the contract between per-tool drawing modules and the generic SVG renderer."""
import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from strutture.shared.sketch import (
    Barre,
    Diagramma,
    Etichetta,
    Freccia,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    campo_schizzo,
    etichetta_quota,
)

pytestmark = pytest.mark.unit


def _plinto() -> Sketch:
    pianta = Vista(titolo="Pianta", forme=(
        Rettangolo(x=0, y=0, w=2.4, h=3.0, stile="calcestruzzo"),
        Rettangolo(x=0.95, y=1.25, w=0.5, h=0.5, stile="evidenza"),
        Quota(p1=(0, 0), p2=(2.4, 0), distanza=-0.4, testo=etichetta_quota("B", 2.4, "m")),
        Barre(centri=((0.2, 0.2), (2.2, 0.2)), diametro=0.016),
    ))
    sezione = Vista(titolo="Sezione", forme=(
        Freccia(coda=(1.2, 1.6), punta=(1.2, 0.8), testo="N = 850 kN"),
        Diagramma(base=((0, 0), (2.4, 0)), valori=(182.0, 96.5), etichette=("182", "96,5")),
        Etichetta(punto=(2.5, 0), simbolo="σ_max", testo="182 kPa"),
    ))
    return Sketch(viste=(pianta, sezione))


def test_sketch_round_trips_through_json_with_discriminated_shapes() -> None:
    sketch = _plinto()
    again = Sketch.model_validate_json(sketch.model_dump_json())
    assert again == sketch
    assert [f.kind for f in again.viste[0].forme] == ["rect", "rect", "dimension", "bars"]


def test_quota_text_uses_italian_decimals() -> None:
    assert etichetta_quota("B", 2.4, "m") == "B = 2,40 m"
    assert etichetta_quota("ø", 16, "mm", decimali=0) == "ø = 16 mm"


def test_shapes_are_validated_and_frozen() -> None:
    with pytest.raises(ValidationError):
        Rettangolo(x=0, y=0, w=0, h=1, stile="calcestruzzo")  # zero width
    with pytest.raises(ValidationError):
        Rettangolo(x=0, y=0, w=1, h=1, stile="rosso")  # styles are semantic, not colours
    with pytest.raises(ValidationError):
        Vista(titolo="vuota", forme=())
    with pytest.raises(ValidationError):
        _plinto().viste[0].titolo = "x"


def test_output_field_helper_carries_the_widget_hint() -> None:
    class Out(BaseModel):
        model_config = ConfigDict(frozen=True)
        schizzo: Sketch | None = campo_schizzo()

    prop = Out.model_json_schema()["properties"]["schizzo"]
    assert prop["widget"] == "sketch" and Out().schizzo is None

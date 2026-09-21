"""Golden test: Rev01 default input->output case, legacy_compat=True (BUILD_CONTRACT §Tests)."""
import pytest

from strutture.members.acciaio_sezione_composta.models import SezioneHRimpiattataInput
from strutture.members.acciaio_sezione_composta.tool import run

pytestmark = pytest.mark.golden

INPUT_ORO = SezioneHRimpiattataInput(
    h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
    piatti=({"b_mm": 8, "h_mm": 105}, {"b_mm": 0, "h_mm": 105}),
    legacy_compat=True,
)


def test_rev01_default_case_matches_cached_sheet_values():
    report = run(INPUT_ORO)
    assert report.ok
    sezione = report.data.sezione

    assert sezione.area_mm2 == pytest.approx(3250.0)
    assert sezione.x_n_mm == pytest.approx(16.54153846153846, rel=1e-6)
    assert sezione.y_n_mm == pytest.approx(57.0, rel=1e-6)
    assert sezione.wpl_x_cm3 == pytest.approx(101.76, rel=1e-6)
    assert sezione.wpl_y_cm3 == pytest.approx(79.73021538461538, rel=1e-6)
    assert sezione.iy_cm4 == pytest.approx(486.08677256410255, rel=1e-6)
    assert sezione.iy_base_cm4 == pytest.approx(230.50208333333336, rel=1e-6)
    assert sezione.rapporto_iy == pytest.approx(486.08677256410255 / 230.50208333333336, rel=1e-6)


def test_rev01_default_case_elements_sum_to_the_section_totals():
    report = run(INPUT_ORO)
    elementi = report.data.elementi
    sezione = report.data.sezione
    assert len(elementi) == 5  # 3 profile elements + A4 + A5 (A5 disabled, area 0)
    assert sum(e.area_mm2 for e in elementi) == pytest.approx(sezione.area_mm2)
    assert sum(e.ix_i_cm4 for e in elementi) == pytest.approx(sezione.ix_cm4, rel=1e-6)
    assert sum(e.iy_i_cm4 for e in elementi) == pytest.approx(sezione.iy_cm4, rel=1e-6)

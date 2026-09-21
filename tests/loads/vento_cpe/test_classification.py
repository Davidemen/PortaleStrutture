import pytest

from strutture.loads.vento_cpe.classification import (
    EDIFICIO_SNELLO,
    EDIFICIO_SNELLO_DIR1,
    EDIFICIO_SNELLO_DIR2,
    EDIFICIO_TOZZO,
    EDIFICIO_TOZZO_LEGACY,
    classify,
)


@pytest.mark.unit
def test_classify_both_squat():
    assert classify(0.75, 0.6) == EDIFICIO_TOZZO


@pytest.mark.unit
def test_classify_default_is_sentence_case_not_all_caps():
    """Design review: "EDIFICIO TOZZO"-style strings must be sentence case in the default
    (code-standard) mode; the raw sheet string is only reproduced under legacy_compat=True."""
    assert classify(0.75, 0.6) == "Edificio tozzo"
    assert not classify(0.75, 0.6).isupper()


@pytest.mark.unit
def test_classify_legacy_compat_reproduces_the_sheets_raw_string():
    assert classify(0.75, 0.6, legacy_compat=True) == EDIFICIO_TOZZO_LEGACY
    assert classify(0.75, 0.6, legacy_compat=True) == "EDIFICIO TOZZO"


@pytest.mark.unit
def test_classify_both_slender():
    assert classify(6.0, 7.0) == EDIFICIO_SNELLO


@pytest.mark.unit
def test_classify_squat_boundary_both_at_threshold():
    assert classify(5.0, 5.0) == EDIFICIO_TOZZO


@pytest.mark.unit
def test_classify_mixed_dir1_slender():
    assert classify(6.0, 4.0) == EDIFICIO_SNELLO_DIR1


@pytest.mark.unit
def test_classify_mixed_dir2_slender():
    assert classify(4.0, 6.0) == EDIFICIO_SNELLO_DIR2

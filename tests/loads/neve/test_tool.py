import pytest

from strutture.loads.neve.models import AccumuloInput, CaricoFaldaInput
from strutture.loads.neve.tool import run_accumulo, run_carico_falda
from strutture.shared.report import CalcError

_FALDA_KWARGS = {
    "as_m": 250,
    "topografia": "Normale",
    "a": 0,
    "parapetto": "NO",
    "a1": 35,
    "parapetto1": "NO",
    "a2": 50,
    "parapetto2": "NO",
}

_ACCUMULO_KWARGS = {"as_m": 249, "topografia": "Normale", "b1": 43.15, "b2": 36.2, "h": 10, "a": 0, "m1_input": 0.8, "msup": 0.45}


@pytest.mark.unit
def test_unknown_comune_raises_calc_error():
    with pytest.raises(CalcError):
        run_carico_falda(CaricoFaldaInput(comune="Nessundove", tipo_copertura="Copertura ad una falda", **_FALDA_KWARGS))


@pytest.mark.unit
def test_bug_4_roof_type_gates_output_only_in_fixed_mode():
    """§7.4 / architecture.md §6: the sheet's `G29` selector is decorative, so legacy mode always
    populates both branches; fixed mode gates the output on the requested roof type.
    """
    legacy = run_carico_falda(
        CaricoFaldaInput(comune="Mapello", tipo_copertura="Copertura ad una falda", legacy_compat=True, **_FALDA_KWARGS)
    ).data
    assert legacy.mu is not None and legacy.mu1 is not None and legacy.mu2 is not None

    una_falda = run_carico_falda(
        CaricoFaldaInput(comune="Mapello", tipo_copertura="Copertura ad una falda", legacy_compat=False, **_FALDA_KWARGS)
    ).data
    assert una_falda.mu is not None
    assert una_falda.mu1 is None and una_falda.qs1 is None and una_falda.mu2 is None and una_falda.qs2 is None

    due_falde = run_carico_falda(
        CaricoFaldaInput(comune="Mapello", tipo_copertura="Copertura a due falde", legacy_compat=False, **_FALDA_KWARGS)
    ).data
    assert due_falde.mu is None and due_falde.qs is None
    assert due_falde.mu1 is not None and due_falde.mu2 is not None


@pytest.mark.unit
def test_bug_2_provincia_keyed_lookup_raises_in_legacy_for_multi_word_provincia():
    """§7.2: `Neve accumulo!H8`'s VLOOKUP is keyed on the *provincia* string, not the comune.
    "Bagno di Romagna"'s provincia is "Forlì-Cesena", which is not itself a comune name -> the
    buggy lookup raises (mirrors the sheet's `#N/A`); the fixed lookup (keyed on comune) succeeds.
    """
    with pytest.raises(CalcError):
        run_accumulo(AccumuloInput(comune="Bagno di Romagna", legacy_compat=True, **_ACCUMULO_KWARGS))

    fixed = run_accumulo(AccumuloInput(comune="Bagno di Romagna", legacy_compat=False, **_ACCUMULO_KWARGS))
    assert fixed.ok
    assert fixed.data.zona == "I (mediterranea)"


@pytest.mark.unit
def test_accumulo_zona_given_directly_skips_comune_lookup():
    report = run_accumulo(AccumuloInput(zona="III", legacy_compat=False, **_ACCUMULO_KWARGS))
    assert report.ok
    assert report.data.zona == "III"


@pytest.mark.unit
def test_accumulo_unknown_comune_raises_calc_error():
    with pytest.raises(CalcError):
        run_accumulo(AccumuloInput(comune="Nessundove", legacy_compat=False, **_ACCUMULO_KWARGS))


@pytest.mark.unit
def test_bug_2_coincidental_success_when_provincia_equals_a_comune_name():
    """Bergamo's provincia is itself named "Bergamo", so the buggy legacy lookup happens to
    resolve to the same zona as the fixed comune-keyed lookup (spec §8 golden case)."""
    legacy = run_accumulo(AccumuloInput(comune="Bergamo", legacy_compat=True, **_ACCUMULO_KWARGS))
    fixed = run_accumulo(AccumuloInput(comune="Bergamo", legacy_compat=False, **_ACCUMULO_KWARGS))
    assert legacy.ok and fixed.ok
    assert legacy.data.zona == fixed.data.zona == "I (alpina)"


@pytest.mark.unit
def test_una_falda_only_a_and_parapetto_is_enough_to_compute():
    """Usability fix: a caller choosing "Copertura ad una falda" must not have to also supply
    the two-pitch fields (previously required by the input model regardless of selection)."""
    report = run_carico_falda(
        CaricoFaldaInput(
            zona="II", as_m=250, topografia="Normale", tipo_copertura="Copertura ad una falda", a=0, parapetto="NO"
        )
    )
    assert report.ok
    assert report.data.mu is not None and report.data.qs is not None
    assert report.data.mu1 is None and report.data.mu2 is None


@pytest.mark.unit
def test_due_falde_only_its_own_fields_is_enough_to_compute():
    report = run_carico_falda(
        CaricoFaldaInput(
            zona="II",
            as_m=250,
            topografia="Normale",
            tipo_copertura="Copertura a due falde",
            a1=35,
            parapetto1="NO",
            a2=50,
            parapetto2="NO",
        )
    )
    assert report.ok
    assert report.data.mu1 is not None and report.data.mu2 is not None
    assert report.data.mu is None

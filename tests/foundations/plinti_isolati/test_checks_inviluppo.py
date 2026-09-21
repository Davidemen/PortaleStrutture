import pytest

from strutture.foundations.plinti_isolati.checks_inviluppo import checks_inviluppo
from strutture.foundations.plinti_isolati.inviluppo import InviluppoRiga
from strutture.foundations.plinti_isolati.rows import ResistenzaRow


@pytest.mark.unit
def test_checks_inviluppo_bearing_pass_fail() -> None:
    inviluppo = (
        InviluppoRiga(grandezza="pressione_max_kpa", famiglia="SLU_STR", valore=150.0, combo="c1", nodo=1),
        InviluppoRiga(grandezza="pressione_max_kpa", famiglia="SLU_EQU", valore=250.0, combo="c2", nodo=1),
    )
    resistenze = (
        ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=200.0),
        ResistenzaRow(famiglia="SLU_EQU", sigma_ammissibile=200.0),
    )
    checks = checks_inviluppo(inviluppo, resistenze, sistema_unita="SI", legacy_compat=False)
    by_name = {c.name: c for c in checks}
    assert by_name["Portanza (SLU_STR)"].passed
    assert not by_name["Portanza (SLU_EQU)"].passed


@pytest.mark.unit
def test_checks_inviluppo_sicurezza_scorrimento_ribaltamento() -> None:
    inviluppo = (
        InviluppoRiga(grandezza="scorrimento_min", famiglia="SLU_STR", valore=0.8, combo="c1", nodo=1),
        InviluppoRiga(grandezza="ribaltamento_x_min", famiglia="SLU_EQU", valore=1.2, combo="c1", nodo=1),
        InviluppoRiga(grandezza="ribaltamento_y_min", famiglia="SLU_EQU", valore=0.5, combo="c1", nodo=1),
        InviluppoRiga(grandezza="area_compressa_min", famiglia="SLU_STR", valore=1.0, combo="c1", nodo=1),
    )
    checks = checks_inviluppo(inviluppo, (), sistema_unita="SI", legacy_compat=False)
    by_name = {c.name: c for c in checks}
    assert not by_name["Scorrimento (SLU_STR)"].passed
    assert by_name["Ribaltamento X (SLU_EQU)"].passed
    assert not by_name["Ribaltamento Y (SLU_EQU)"].passed
    assert "area_compressa_min" not in [c.name for c in checks]  # no numeric threshold defined, not a Check


@pytest.mark.unit
def test_checks_inviluppo_ribaltamento_solo_famiglie_equ_no_legacy() -> None:
    """Fix (HIGH, review finding gamma_azioni.py): overturning is an EQU-type verification
    (NTC2018 Tab. 2.6.I, gammaG1=0.9 stabilising); `SLU_STR`'s self-weight uses gammaW=1.35
    instead, inflating Mstab by 50%, so its overturning check is suppressed in the fixed mode."""
    inviluppo = (
        InviluppoRiga(grandezza="ribaltamento_x_min", famiglia="SLU_STR", valore=1.2, combo="c1", nodo=1),
        InviluppoRiga(grandezza="ribaltamento_x_min", famiglia="SLU_EQU", valore=0.5, combo="c2", nodo=1),
        InviluppoRiga(grandezza="ribaltamento_x_min", famiglia="SLV_EQU", valore=2.0, combo="c3", nodo=1),
    )
    checks = checks_inviluppo(inviluppo, (), sistema_unita="SI", legacy_compat=False)
    names = [c.name for c in checks]
    assert "Ribaltamento X (SLU_STR)" not in names
    assert "Ribaltamento X (SLU_EQU)" in names
    assert "Ribaltamento X (SLV_EQU)" in names


@pytest.mark.unit
def test_checks_inviluppo_ribaltamento_tutte_famiglie_legacy() -> None:
    """`legacy_compat=True` keeps emitting the check for every family (sheet behaviour)."""
    inviluppo = (InviluppoRiga(grandezza="ribaltamento_x_min", famiglia="SLU_STR", valore=1.2, combo="c1", nodo=1),)
    checks = checks_inviluppo(inviluppo, (), sistema_unita="SI", legacy_compat=True)
    assert "Ribaltamento X (SLU_STR)" in [c.name for c in checks]


@pytest.mark.unit
def test_checks_inviluppo_portanza_clausola_non_ntc() -> None:
    """Fix (MEDIUM, review finding): bearing here is a plain user-supplied allowable-stress
    comparison (no qlim/Meyerhof effective-area/gammaR=2.3 calculation), so it must not be
    stamped with the NTC2018 §6.4.2.1 limit-state clause."""
    inviluppo = (InviluppoRiga(grandezza="pressione_max_kpa", famiglia="SLU_STR", valore=100.0, combo="c1", nodo=1),)
    resistenze = (ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=200.0),)
    checks = checks_inviluppo(inviluppo, resistenze, sistema_unita="SI", legacy_compat=False)
    assert checks[0].clause != "NTC2018 §6.4.2.1"


@pytest.mark.unit
def test_checks_inviluppo_famiglia_senza_resistenza_omessa() -> None:
    """A family present in the envelope but not in `resistenze` produces no bearing check (the
    input validator already rejects this at the tool boundary; defensive here)."""
    inviluppo = (InviluppoRiga(grandezza="pressione_max_kpa", famiglia="SLE_QP", valore=100.0, combo="c1", nodo=1),)
    checks = checks_inviluppo(inviluppo, (), sistema_unita="SI", legacy_compat=False)
    assert checks == ()


@pytest.mark.unit
def test_checks_inviluppo_conversione_tecnico() -> None:
    """A `resistenze` value given in kg/cm2 (`sistema_unita='tecnico'`) is converted to kPa once,
    at the boundary (§9-D1)."""
    inviluppo = (InviluppoRiga(grandezza="pressione_max_kpa", famiglia="SLU_STR", valore=196.133, combo="c1", nodo=1),)
    resistenze = (ResistenzaRow(famiglia="SLU_STR", sigma_ammissibile=2.0),)  # 2 kg/cm2 = 196.133 kPa
    checks = checks_inviluppo(inviluppo, resistenze, sistema_unita="tecnico", legacy_compat=False)
    assert checks[0].passed
    assert checks[0].limit == pytest.approx(196.133, rel=1e-4)

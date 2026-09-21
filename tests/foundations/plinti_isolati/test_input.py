"""Boundary/validation tests for the optional "Terreno" input block (docs/architecture-phase4.md
§C "Integration"): `terreno_condizione` absent = block empty, no other `terreno_*` field required;
once set, the fields the chosen `condizione` needs become mandatory."""
import pytest

from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

_SCALARI: dict = {
    "ax_m": 2.0, "by_m": 2.0, "h_plinto_m": 0.6, "h_interro_m": 1.0,
    "copriferro_cm": 5.0, "passo_armatura_cm": 15.0,
    "resistenze": ({"famiglia": "SLU_STR", "sigma_ammissibile": 2.0},),
    "reazioni": ({"nodo": 1, "combo": "C1", "famiglia": "SLU_STR",
                  "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 300.0, "mx_kNm": 0.0, "my_kNm": 0.0, "mz_kNm": 0.0},),
}


@pytest.mark.unit
def test_input_blocco_terreno_vuoto_accettato() -> None:
    inputs = PlintoIsolatoInput(**_SCALARI)
    assert inputs.terreno_condizione is None


@pytest.mark.unit
def test_input_blocco_terreno_drenata_senza_phi_rifiutato() -> None:
    with pytest.raises(ValueError, match="terreno_phi_k_deg"):
        PlintoIsolatoInput(**_SCALARI, terreno_condizione="drenata", terreno_c_k_kpa=0.0, terreno_gamma_kn_m3=18.0)


@pytest.mark.unit
def test_input_blocco_terreno_drenata_senza_c_rifiutato() -> None:
    with pytest.raises(ValueError, match="terreno_phi_k_deg"):
        PlintoIsolatoInput(**_SCALARI, terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_gamma_kn_m3=18.0)


@pytest.mark.unit
def test_input_blocco_terreno_non_drenata_senza_cu_rifiutato() -> None:
    with pytest.raises(ValueError, match="terreno_cu_k_kpa"):
        PlintoIsolatoInput(**_SCALARI, terreno_condizione="non_drenata", terreno_gamma_kn_m3=18.0)


@pytest.mark.unit
def test_input_blocco_terreno_senza_gamma_rifiutato() -> None:
    with pytest.raises(ValueError, match="terreno_gamma_kn_m3"):
        PlintoIsolatoInput(**_SCALARI, terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_c_k_kpa=0.0)


@pytest.mark.unit
def test_input_blocco_terreno_drenata_completo_accettato() -> None:
    inputs = PlintoIsolatoInput(**_SCALARI, terreno_condizione="drenata", terreno_phi_k_deg=30.0,
                                 terreno_c_k_kpa=0.0, terreno_gamma_kn_m3=18.0)
    assert inputs.terreno_condizione == "drenata"


@pytest.mark.unit
def test_input_blocco_terreno_non_drenata_completo_accettato() -> None:
    inputs = PlintoIsolatoInput(**_SCALARI, terreno_condizione="non_drenata", terreno_cu_k_kpa=50.0,
                                 terreno_gamma_kn_m3=18.0)
    assert inputs.terreno_condizione == "non_drenata"


@pytest.mark.unit
def test_input_blocco_terreno_falda_resta_opzionale() -> None:
    """`terreno_profondita_falda_m` resta opzionale anche a blocco compilato (falda assente)."""
    inputs = PlintoIsolatoInput(**_SCALARI, terreno_condizione="drenata", terreno_phi_k_deg=30.0,
                                 terreno_c_k_kpa=0.0, terreno_gamma_kn_m3=18.0)
    assert inputs.terreno_profondita_falda_m is None

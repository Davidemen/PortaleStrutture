"""`capacita_portante` / `checks_capacita_portante` — composition over `reazioni`, per-famiglia
envelope, governing row and the single envelope-level check (docs/architecture-phase4.md §C)."""
import pytest

from strutture.foundations.plinti_isolati.capacita_portante import (
    AVVISO_BLOCCO_IGNORATO_LEGACY,
    AVVISO_SISMICO,
    CapacitaPortanteOutput,
    capacita_portante,
)
from strutture.foundations.plinti_isolati.capacita_portante_checks import checks_capacita_portante
from strutture.foundations.plinti_isolati.capacita_portante_riga import RigaCapacitaPortante
from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput
from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica

_SCALARI: dict = {
    "ax_m": 2.0, "by_m": 2.0, "h_plinto_m": 0.6, "h_interro_m": 1.0,
    "copriferro_cm": 5.0, "passo_armatura_cm": 15.0,
    "resistenze": ({"famiglia": "SLU_STR", "sigma_ammissibile": 2.0},
                    {"famiglia": "SLV_STR", "sigma_ammissibile": 2.0}),
}


def _reazione(**overrides) -> dict:
    base = {"nodo": 1, "combo": "C1", "famiglia": "SLU_STR",
            "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 300.0, "mx_kNm": 0.0, "my_kNm": 0.0, "mz_kNm": 0.0}
    return {**base, **overrides}


def _inputs(**overrides) -> PlintoIsolatoInput:
    return PlintoIsolatoInput(**{**_SCALARI, "reazioni": (_reazione(),), **overrides})


def _righe_verifica(inputs: PlintoIsolatoInput):
    return tuple(
        riga_verifica(
            row, inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.h_interro_m,
            inputs.a_pedestal_m, inputs.b_pedestal_m, inputs.h_pedestal_sopra_m, inputs.h_pedestal_sotto_m,
            inputs.offset_leva_m, inputs.ex_m, inputs.ey_m, inputs.gamma_terreno_kNm3, inputs.phi_terreno_deg,
            metodo_pressioni=inputs.metodo_pressioni, legacy_compat=inputs.legacy_compat,
        )
        for row in inputs.reazioni
    )


@pytest.mark.unit
def test_capacita_portante_blocco_vuoto() -> None:
    """`terreno_condizione` assente = blocco vuoto: nessuna riga, nessun avviso."""
    inputs = _inputs()
    righe = _righe_verifica(inputs)
    output, avvisi = capacita_portante(righe, inputs)
    assert output == CapacitaPortanteOutput()
    assert avvisi == ()


@pytest.mark.unit
def test_capacita_portante_blocco_compilato() -> None:
    inputs = _inputs(terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_c_k_kpa=0.0,
                      terreno_gamma_kn_m3=18.0)
    righe = _righe_verifica(inputs)
    output, avvisi = capacita_portante(righe, inputs)
    assert len(output.righe) == 1
    assert isinstance(output.righe[0], RigaCapacitaPortante)
    assert output.governante is not None
    assert output.governante.ratio == output.righe[0].ratio
    assert len(output.inviluppo) == 1  # una sola famiglia (SLU_STR) nella tabella reazioni
    assert avvisi == ()  # SLU_STR non è una famiglia sismica


@pytest.mark.unit
def test_capacita_portante_famiglia_sismica_avviso() -> None:
    inputs = _inputs(
        terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_c_k_kpa=0.0, terreno_gamma_kn_m3=18.0,
        reazioni=(_reazione(famiglia="SLV_STR"),),
        resistenze=({"famiglia": "SLV_STR", "sigma_ammissibile": 2.0},),
    )
    righe = _righe_verifica(inputs)
    _, avvisi = capacita_portante(righe, inputs)
    assert avvisi == (AVVISO_SISMICO,)


@pytest.mark.unit
def test_capacita_portante_legacy_ignora_il_blocco() -> None:
    inputs = _inputs(terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_c_k_kpa=0.0,
                      terreno_gamma_kn_m3=18.0, legacy_compat=True)
    righe = _righe_verifica(inputs)
    output, avvisi = capacita_portante(righe, inputs)
    assert output == CapacitaPortanteOutput()
    assert avvisi == (AVVISO_BLOCCO_IGNORATO_LEGACY,)


@pytest.mark.unit
def test_checks_capacita_portante_vuoto_senza_governante() -> None:
    assert checks_capacita_portante(CapacitaPortanteOutput()) == ()


@pytest.mark.unit
def test_checks_capacita_portante_pass_fail() -> None:
    riga = RigaCapacitaPortante(nodo=1, combo="C1", famiglia="SLU_STR", q_lim_kpa=500.0, r_d_kn=1000.0,
                                 n_ed_kn=300.0, ratio=0.3, b_eff_m=2.0, l_eff_m=2.0)
    checks = checks_capacita_portante(CapacitaPortanteOutput(righe=(riga,), governante=riga))
    assert len(checks) == 1
    assert checks[0].passed
    assert checks[0].clause == "NTC2018 §6.4.2.1, EN 1997-1 Annesso D"
    assert checks[0].value == 300.0 and checks[0].limit == 1000.0

    riga_bocciata = riga.model_copy(update={"ratio": 1.5, "n_ed_kn": 1500.0})
    checks_ko = checks_capacita_portante(CapacitaPortanteOutput(righe=(riga_bocciata,), governante=riga_bocciata))
    assert not checks_ko[0].passed

import json
from pathlib import Path

import pytest

from strutture.members.ca_punzonamento.compose import run
from strutture.members.ca_punzonamento.models import PunzonamentoInput

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_punzonamento_oracle.json").read_text(encoding="utf-8"))
# Case F (index 5): tight rebar spacing pushes rho_l above 2%. shared.ec2_shear.v_rd_c always caps
# rho_l at 2% (EC2 §6.4.4(1)) even under legacy_compat=True (docs/divergences/ca-punzonamento.md,
# "D35/D37 (rho cap)"), so every rho-dependent cell downstream of D37 legitimately diverges from the
# sheet for this one case; it gets its own dedicated test below instead of the generic loop.
CASES_MATCHING_SHEET_EXACTLY = FIXTURE[:5]

# D13 dropdown -> posizione enum (tables.POSIZIONE_BETA)
BETA_TO_POSIZIONE = {1.0: "centrato", 1.15: "interno", 1.4: "bordo", 1.5: "angolo"}


def _inputs(case: dict) -> PunzonamentoInput:
    i = case["inputs"]
    return PunzonamentoInput(
        ved_kN=i["D2"], pterreno_MPa=i["D3"], lato_a_mm=i["D4"], lato_b_mm=i["D5"], h_mm=i["D6"],
        diametro_mm=i["D7"], fck_MPa=i["D8"], copriferro_mm=i["D9"], posizione=BETA_TO_POSIZIONE[i["D13"]],
        umanuale_mm=None if i["D21"] == "x" else i["D21"], a_amanuale_mm2=None if i["D24"] == "x" else i["D24"],
        px_mm=i["D27"], py_mm=i["D28"], phix_mm=i["D29"], phiy_mm=i["D30"], paddx_mm=i["D31"], paddy_mm=i["D32"],
        phiaddx_mm=i["D33"], phiaddy_mm=i["D34"], a1eff_mm=i["D46"], bu_mm=i["D47"], st_mm=i["D52"],
        phi_staffa_mm=i["D55"], n_staffe=i["D58"], legacy_compat=True,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("case", CASES_MATCHING_SHEET_EXACTLY, ids=range(len(CASES_MATCHING_SHEET_EXACTLY)))
def test_oracle_case(case: dict):
    outputs = case["outputs"]
    report = run(_inputs(case))
    assert report.ok
    data = report.data

    assert data.geometria.dx_mm == pytest.approx(outputs["D10"], rel=1e-6)
    assert data.geometria.dy_mm == pytest.approx(outputs["D11"], rel=1e-6)
    assert data.geometria.d_mm == pytest.approx(outputs["D12"], rel=1e-6)
    assert data.geometria.u0_mm == pytest.approx(outputs["D16"], rel=1e-6)

    assert data.faccia_pilastro.v_rd_max_MPa == pytest.approx(outputs["D17"], rel=1e-6)
    assert data.faccia_pilastro.v_ed_0_MPa == pytest.approx(outputs["D18"], rel=1e-5)
    assert (data.faccia_pilastro.v_ed_0_MPa < data.faccia_pilastro.v_rd_max_MPa) == (outputs["F18"] == "Verificato")

    pc = data.perimetro_critico
    assert pc.a_governante_su_d == pytest.approx(outputs["AX154"], rel=1e-6)
    assert pc.ui_mm == pytest.approx(outputs["D22"], rel=1e-5)
    assert pc.area_mm2 == pytest.approx(outputs["D23"], rel=1e-5)
    assert pc.k == pytest.approx(outputs["D26"], rel=1e-6)
    assert pc.rho == pytest.approx(outputs["D35"], rel=1e-5)
    assert pc.v_rd_i_MPa == pytest.approx(outputs["D37"], rel=1e-5)
    assert pc.v_ed_i_MPa == pytest.approx(outputs["D38"], rel=1e-4)
    assert pc.rapporto == pytest.approx(outputs["D38"] / outputs["D37"], rel=1e-5)
    assert pc.armatura_necessaria == (outputs["F38"] != "Verificato")

    riga_050, riga_125, riga_200 = pc.righe[0], pc.righe[75], pc.righe[-1]
    for riga, prefix in ((riga_050, "2"), (riga_125, "77"), (riga_200, "152")):
        assert riga.a_mm == pytest.approx(outputs[f"AQ{prefix}"], rel=1e-5)
        assert riga.ui_mm == pytest.approx(outputs[f"AR{prefix}"], rel=1e-5)
        assert riga.area_mm2 == pytest.approx(outputs[f"AS{prefix}"], rel=1e-4)
        assert riga.v_rd_i_MPa == pytest.approx(outputs[f"AU{prefix}"], rel=1e-4)
        assert riga.v_ed_i_MPa == pytest.approx(outputs[f"AV{prefix}"], rel=1e-4)
        assert riga.rapporto == pytest.approx(outputs[f"AW{prefix}"], rel=1e-4)

    assert data.messaggio.upper().startswith("PROGETTO") or "NON SODDISFATTA" in data.messaggio.upper()

    armatura = data.armatura
    assert armatura is not None  # legacy_compat=True: always present
    assert armatura.u0_out_mm == pytest.approx(outputs["D41"], rel=1e-5)
    assert armatura.sr_max_mm == pytest.approx(outputs["D43"], rel=1e-6)
    assert armatura.a1_min_mm == pytest.approx(outputs["D44"], rel=1e-6)
    assert armatura.a1_max_mm == pytest.approx(outputs["D45"], rel=1e-6)
    assert armatura.sr_mm == pytest.approx(outputs["D51"], rel=1e-4)
    assert armatura.asw_min_mm2 == pytest.approx(outputs["D53"], rel=1e-4)
    assert armatura.fywd_ef_MPa == pytest.approx(outputs["H56"], rel=1e-6)
    assert armatura.area_staffa_mm2 == pytest.approx(outputs["H55"], rel=1e-6)
    assert armatura.v_rd_cs1_kN == pytest.approx(outputs["D56"], rel=1e-5)
    assert armatura.v_rd_c_primo_kN == pytest.approx(outputs["D59"], rel=1e-5)
    assert armatura.v_rd_s_kN == pytest.approx(outputs["D60"], rel=1e-5)
    assert armatura.v_rrd_kN == pytest.approx(outputs["D61"], rel=1e-5)
    ved_beta = case["inputs"]["D2"] * case["inputs"]["D13"]
    assert (armatura.v_rrd_kN > ved_beta) == (outputs["F61"] == "Verificato")
    assert armatura.ved_su_vrd == pytest.approx(outputs["D62"], rel=1e-5)


@pytest.mark.oracle
def test_oracle_scan_matches_governing_row_index():
    """Case B (index 1): pterreno>0 breaks monotonicity, governing a/d != 2.0 (spec §7.6)."""
    case = FIXTURE[1]
    outputs = case["outputs"]
    assert outputs["AX154"] != pytest.approx(2.0)
    report = run(_inputs(case))
    assert report.data.perimetro_critico.a_governante_su_d == pytest.approx(outputs["AX154"], rel=1e-6)


@pytest.mark.oracle
def test_oracle_case_needs_reinforcement():
    """Case E (index 4): Ved raised until F38 fails and the armatura block becomes meaningful."""
    case = FIXTURE[4]
    assert case["outputs"]["F38"] != "Verificato"
    report = run(_inputs(case))
    assert report.data.perimetro_critico.armatura_necessaria is True
    assert report.data.armatura.n_file >= 2


@pytest.mark.oracle
def test_oracle_case_rho_cap_diverges_from_sheet():
    """Case F (index 5): rho_l > 2%. Geometry/rho itself still match the sheet exactly; v_rd_i
    diverges because shared.ec2_shear.v_rd_c always caps rho_l at 2% (docs/divergences/
    ca-punzonamento.md), even under legacy_compat=True."""
    case = FIXTURE[5]
    outputs = case["outputs"]
    report = run(_inputs(case))
    data = report.data

    assert data.geometria.d_mm == pytest.approx(outputs["D12"], rel=1e-6)
    assert data.perimetro_critico.rho == pytest.approx(outputs["D35"], rel=1e-5)
    assert data.perimetro_critico.rho > 0.02

    sheet_v_rd_i = outputs["D37"]
    assert data.perimetro_critico.v_rd_i_MPa < sheet_v_rd_i  # capped rho -> lower capacity
    assert data.perimetro_critico.v_rd_i_MPa == pytest.approx(sheet_v_rd_i, rel=0.06)  # same order of magnitude

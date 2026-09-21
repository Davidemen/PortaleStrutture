import json
from pathlib import Path

import pytest

from strutture.members.ca_travi.models import TraveRettangolareInput
from strutture.members.ca_travi.tool import run
from strutture.shared.report import CalcError

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_travi_rettangolare_oracle.json").read_text())

_OK = "OK"


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs, outputs = case["inputs"], case["outputs"]
    def build_inputs() -> TraveRettangolareInput:
        return TraveRettangolareInput(
            b_mm=inputs["H6"], h_mm=inputs["H7"], tipo_acciaio=inputs["H8"], tipo_cls=inputs["H9"],
            copriferro_mm=inputs["H10"], n_ferri1=inputs["H11"], diametro_ferri1_mm=inputs["H12"],
            n_ferri2=inputs["H13"], diametro_ferri2_mm=inputs["H14"],
            diametro_staffe1_mm=inputs["H15"], passo_staffe1_mm=inputs["H16"], n_bracci_staffe1=inputs["H17"],
            diametro_staffe2_mm=inputs["H18"], n_bracci_staffe2=inputs["H20"], alpha_staffe_deg=inputs["Z23"],
            ved_kN=inputs["H23"], med_slu_kNm=inputs["H24"], med_rara_kNm=inputs["H25"], med_qp_kNm=inputs["H26"],
            condizioni_ambientali=inputs["Y50"], combinazione=inputs["Y51"], sensibilita_armatura=inputs["Y52"],
            classe_apertura_fessura=inputs["Z54"],
            classe_duttilita=inputs["J58"], mrc_kNm=inputs["K78"], lt_m=inputs["K80"], legacy_compat=True,
        )

    if outputs["Z22"] == "#NUM!":
        # over-reinforced-for-shear input combination: the sheet itself errors out (#NUM!,
        # sqrt of a negative number); our code raises CalcError for the same condition.
        with pytest.raises(CalcError):
            run(build_inputs())
        return

    report = run(build_inputs())
    assert report.ok
    data = report.data

    assert data.armatura.as_min_mm2 == pytest.approx(outputs["Z12"], rel=1e-5)
    assert (data.armatura.as_o_mm2 >= data.armatura.as_min_mm2) == (outputs["Y13"] == _OK)
    assert data.armatura.as_max_mm2 == pytest.approx(outputs["Z14"], rel=1e-6)
    assert (data.armatura.as_o_mm2 <= data.armatura.as_max_mm2) == (outputs["Y15"] == _OK)
    assert data.armatura.ast_min_per_m_mm2 == pytest.approx(outputs["Z16"], rel=1e-5)
    assert (data.armatura.asw_per_m_mm2 >= data.armatura.ast_min_per_m_mm2) == (outputs["Y17"] == _OK)
    assert data.armatura.passo_max_staffe_mm == pytest.approx(outputs["Z18"], rel=1e-5)
    assert (inputs["H16"] <= data.armatura.passo_max_staffe_mm) == (outputs["Y19"] == _OK)

    assert data.taglio.cotg_theta == pytest.approx(outputs["Z22"], rel=1e-5)
    assert data.taglio.vrdc_kN == pytest.approx(outputs["Z24"], rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(outputs["Z25"], rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(outputs["Z26"], rel=1e-5)
    assert (data.taglio.vrd_kN > inputs["H23"]) == (outputs["Y27"] == _OK)

    assert data.flessione.d_mm == pytest.approx(outputs["Z31"], rel=1e-6)
    assert data.flessione.y_mm == pytest.approx(outputs["Z32"], rel=1e-5)
    assert data.flessione.mrd_kNm == pytest.approx(outputs["Z33"], rel=1e-5)
    assert (data.flessione.mrd_kNm > inputs["H24"]) == (outputs["Y34"] == _OK)
    assert data.flessione.tasso_sfruttamento == pytest.approx(outputs["Z35"], rel=1e-5)

    assert data.sle_tensioni.x_mm == pytest.approx(outputs["Z38"], rel=1e-5)
    assert data.sle_tensioni.sigma_c_rara_MPa == pytest.approx(outputs["Z39"], rel=1e-5)
    assert (data.sle_tensioni.sigma_c_rara_MPa < data.sle_tensioni.limite_sigma_c_rara_MPa) == (outputs["Y40"] == _OK)
    assert data.sle_tensioni.sigma_s_rara_MPa == pytest.approx(outputs["Z41"], rel=1e-5)
    assert (data.sle_tensioni.sigma_s_rara_MPa < data.sle_tensioni.limite_sigma_s_MPa) == (outputs["Y42"] == _OK)
    assert data.sle_tensioni.sigma_c_qp_MPa == pytest.approx(outputs["Z46"], rel=1e-5)
    assert (data.sle_tensioni.sigma_c_qp_MPa < data.sle_tensioni.limite_sigma_c_qp_MPa) == (outputs["Y47"] == _OK)
    assert data.sle_tensioni.sigma_s_combinazione_MPa == pytest.approx(outputs["Z53"], rel=1e-5)

    assert data.fessurazione.sigma_limite_MPa == pytest.approx(outputs["AI54"], rel=1e-5)
    assert (data.sle_tensioni.sigma_s_combinazione_MPa < data.fessurazione.sigma_limite_MPa) == (outputs["Y55"] == _OK)

    assert data.dettagli_costruttivi.lunghezza_critica_mm == pytest.approx(outputs["K59"], rel=1e-6)
    assert data.dettagli_costruttivi.passo_max_zona_critica_mm == pytest.approx(outputs["K60"], rel=1e-5, abs=1e-9)
    assert data.dettagli_costruttivi.lunghezza_ancoraggio_mm == pytest.approx(outputs["K62"], rel=1e-6)
    assert data.dettagli_costruttivi.ved_max_kN == pytest.approx(outputs["K81"], rel=1e-5)
    assert (data.dettagli_costruttivi.ved_max_kN < data.taglio.vrd_kN) == (outputs["J82"] == _OK)

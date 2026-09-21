"""Golden-case test against the source workbook's own cached values (docs/specs/fond-plinti-pali.md
"Golden test case", cross-checked cell-by-cell against `build/data/fond-plinti-pali/footing-check.csv`
— the workbook's last LibreOffice recalculation, i.e. the same data `extract.fixtures.generate`
would recompute). `legacy_compat=True` throughout, per contract."""
import pytest

from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


@pytest.fixture
def report(golden_inputs: dict):
    result = execute(TOOL, golden_inputs)
    assert result.ok, result.errors
    return result.data


@pytest.mark.golden
def test_inviluppo(report) -> None:
    per_grandezza = {r.grandezza: r for r in report.inviluppo}
    assert per_grandezza["n_pila_min"].valore == pytest.approx(244.23565735, rel=1e-6)  # Footing check!AF12
    assert per_grandezza["n_pila_max"].valore == pytest.approx(896.06124265, rel=1e-6)  # AG12
    assert per_grandezza["mx_max"].valore == pytest.approx(790.5519458, rel=1e-6)  # AZ13
    assert per_grandezza["mx_min"].valore == pytest.approx(-790.5519458, rel=1e-6)  # AZ14
    assert per_grandezza["my_max"].valore == pytest.approx(862.4196368, rel=1e-6)  # AV13
    assert per_grandezza["my_min"].valore == pytest.approx(-862.4196368, rel=1e-6)  # AV14
    assert per_grandezza["n_totale_max"].valore == pytest.approx(1899.9593, rel=1e-6)  # AV7
    assert per_grandezza["n_totale_min"].valore == pytest.approx(847.1593, rel=1e-6)  # AV36
    assert report.n_max_pila_kN == pytest.approx(896.06124265, rel=1e-6)


@pytest.mark.golden
def test_puntoni_tiranti(report) -> None:
    puntone = report.puntoni_tiranti.puntone
    assert puntone.lxy_m == pytest.approx(1.4142135623730951, rel=1e-9)  # BG5
    assert puntone.h_wt2_m == pytest.approx(1.11, rel=1e-6)  # BG6
    assert puntone.theta_deg == pytest.approx(38.1279617063314, rel=1e-6)  # BG8
    assert puntone.wt_mm == pytest.approx(180.0, rel=1e-6)  # BG17
    assert puntone.ws_mm == pytest.approx(512.0459908268137, rel=1e-6)  # BG18
    assert puntone.acs_mm2 == pytest.approx(262191.09672181343, rel=1e-6)  # BG19
    assert puntone.fus_kN == pytest.approx(1451.2997117682783, rel=1e-6)  # BG9
    assert puntone.sigma_rd_max_MPa == pytest.approx(13.914794666666667, rel=1e-6)  # BG12
    assert puntone.fns_kN == pytest.approx(3648.335274312174, rel=1e-6)  # BG21
    assert puntone.verificato is True
    assert puntone.utilizzo == pytest.approx(0.39779779067643223, rel=1e-6)  # BI22

    tirante_xy = report.puntoni_tiranti.tirante_xy
    assert tirante_xy is not None
    assert tirante_xy.fut_kN == pytest.approx(456.6565629090159, rel=1e-6)  # BL10
    assert tirante_xy.at_mm2 == pytest.approx(1608.495438637974, rel=1e-6)  # BL22
    assert tirante_xy.fnt_kN == pytest.approx(629.4112585974682, rel=1e-6)  # BL23
    assert tirante_xy.utilizzo == pytest.approx(0.725529702037098, rel=1e-6)  # BN24

    for tirante_ortho in (report.puntoni_tiranti.tirante_x, report.puntoni_tiranti.tirante_y):
        assert tirante_ortho is not None
        assert tirante_ortho.fut_kN == pytest.approx(615.7343206352589, rel=1e-6)  # BL13/BL14
        assert tirante_ortho.at_mm2 == pytest.approx(3619.1147369354417, rel=1e-6)  # BL32/BL43
        assert tirante_ortho.fnt_kN == pytest.approx(1416.1753318443034, rel=1e-6)  # BL34/BL45
        assert tirante_ortho.utilizzo == pytest.approx(0.43478678578123525, rel=1e-6)  # BN35/BN46


@pytest.mark.golden
def test_flessione(report) -> None:
    for inf in (report.flessione.inf_x, report.flessione.inf_y):
        assert inf.as_min_mm2 == pytest.approx(2160.0, rel=1e-9)  # AV5/AZ5
        assert inf.as_prov_mm2 == pytest.approx(4523.893421169302, rel=1e-6)  # AV28/AZ28
    assert report.flessione.inf_x.mu_kNm == pytest.approx(1485.0100570500001, rel=1e-6)  # AV15
    assert report.flessione.inf_x.as_req_flexural_mm2 == pytest.approx(3406.66580013465, rel=1e-6)  # AV20
    assert report.flessione.inf_y.mu_kNm == pytest.approx(1413.1424768000002, rel=1e-6)  # AZ15
    assert report.flessione.inf_y.as_req_flexural_mm2 == pytest.approx(3241.799019190106, rel=1e-6)  # AZ20

    # The sheet uses a fixed "diam_assumed" (20mm, `AV42`) for the top effective depth `d`,
    # independent of the final bar diameter it happens to report (`AV50`, 24mm here) — a two-diam
    # split this simplified/excluded-from-report top block does not replicate (see divergences doc);
    # `_progetta` uses one diameter for both, so `as_req_flexural`/`d` differ slightly (~0.5%) from
    # the sheet's own AV43/AZ43 while `mu_kNm`/`as_min_mm2`/`as_prov_mm2` (which do not depend on
    # this) still match exactly.
    for sup in (report.flessione.sup_x, report.flessione.sup_y):
        assert sup.mu_kNm == pytest.approx(211.789825, rel=1e-6)  # AV38/AZ38
        assert sup.as_min_mm2 == pytest.approx(1080.0, rel=1e-9)  # AV34/AZ34
        assert sup.as_req_flexural_mm2 == pytest.approx(483.2505927579365, rel=1e-2)  # AV43/AZ43
        assert sup.as_prov_mm2 == pytest.approx(2260.8, rel=1e-6)  # AV51/AZ51 (legacy literal 3.14)


@pytest.mark.golden
def test_taglio_punzonamento(report) -> None:
    taglio = report.taglio
    assert taglio.d_mm == pytest.approx(1102.0, rel=1e-9)  # AR86
    assert taglio.ved_kN == pytest.approx(1537.33005, rel=1e-6)  # AR96
    assert taglio.ved_ridotto_kN == pytest.approx(327.83354060798547, rel=1e-6)  # AR98
    assert taglio.k == pytest.approx(1.426014322842305, rel=1e-6)  # AR99 (unclamped, legacy)
    assert taglio.rho == pytest.approx(0.0010262916109730722, rel=1e-6)  # AR100
    assert taglio.vrd_c_MPa == pytest.approx(0.33715442570424187, rel=1e-6)  # MAX(AR101,AR102)
    assert taglio.vrd_c_kN == pytest.approx(1486.1767085042982, rel=1e-6)  # AR103
    assert taglio.utilizzo == pytest.approx(0.22058853347117796, rel=1e-6)  # AR104
    assert taglio.verificato is True

    punzonamento = report.punzonamento
    assert punzonamento.u_mm == pytest.approx(2800.0, rel=1e-9)  # AR110
    assert punzonamento.vrd_max_kN == pytest.approx(17220.116479999997, rel=1e-6)  # AR111
    assert punzonamento.utilizzo == pytest.approx(0.17855048213936356, rel=1e-6)  # AR112 (Nsd/VRd,max)
    assert punzonamento.interasse_x_sufficiente is True  # AS108 "OK" (2000 > 1800)
    assert punzonamento.interasse_y_sufficiente is True  # AS109 "OK"

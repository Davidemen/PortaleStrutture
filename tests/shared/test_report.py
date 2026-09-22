

def test_success_keeps_only_field_references_of_warnings_that_exist() -> None:
    from pydantic import BaseModel

    from strutture.shared.report import success

    class In(BaseModel):
        x: float = 1.0

    report = success({"a": 1}, In(), warnings=("Manca V_g.",), avvisi_campi={"Manca V_g.": "v_gravita_kN", "Altro.": "x"})
    assert report.avvisi_campi == {"Manca V_g.": "v_gravita_kN"}
    assert success({"a": 1}, In()).avvisi_campi == {}

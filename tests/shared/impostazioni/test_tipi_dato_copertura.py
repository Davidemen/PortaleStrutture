"""Coverage table (§26.4): every numeric input of every discovered tool gets a type verdict, and the
three diameters the spec names explicitly (section/pile) stay lengths, not `diametro_armatura`."""
import pytest

from strutture.shared.impostazioni.campi import campi_numerici
from strutture.shared.impostazioni.tipi_dato import tipo_dato
from strutture.shared.tool import discover

_TIPI_VALIDI = {
    "lunghezza_m", "lunghezza_cm", "lunghezza_mm", "diametro_armatura", "passo_armatura", "copriferro",
    "spessore", "intero", None,
}


@pytest.mark.unit
def test_every_numeric_field_of_every_tool_classifies_cleanly():
    tools = discover()
    assert tools, "nessuno strumento scoperto: controllare TOOL_PACKAGES"
    for tool in tools.values():
        for nome, schema_campo in campi_numerici(tool):
            assert tipo_dato(nome, schema_campo) in _TIPI_VALIDI, f"{tool.name}.{nome}"


@pytest.mark.unit
def test_section_and_pile_diameters_stay_lengths():
    tools = discover()
    casi = {
        "ca-punzonamento": "diametro_mm",
        "ca-sezione-dominio-mn": "diametro_mm",
        "fond-plinto-su-pali": "diametro_pila_mm",
    }
    for nome_strumento, campo in casi.items():
        tool = tools.get(nome_strumento)
        if tool is None:
            continue  # tool not built in this checkout: nothing to assert
        campi = dict(campi_numerici(tool))
        if campo not in campi:
            continue
        assert tipo_dato(campo, campi[campo]) != "diametro_armatura", f"{nome_strumento}.{campo}"

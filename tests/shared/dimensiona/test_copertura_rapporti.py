"""WORKBENCH_SPEC §23.2: `Check`s produced by the tools' own examples that carry no `value`/`limit`
ratio are frozen to a known list. A new one appearing means a new tool (or a new check on an
existing tool) needs a "Dimensiona" decision — this test fails loudly instead of the search
silently treating it as outcome-only without anyone noticing."""
from strutture.shared.dimensiona.sfruttamento import rapporto
from strutture.shared.tool import discover, execute

_ATTESE_SENZA_RAPPORTO = frozenset({
    ("ca-pilastro-rettangolare", "Percentuale di armatura longitudinale"),
    ("ca-pilastro-rettangolare", "Verifica di snellezza"),
    ("ca-pilastro-rettangolare", "Diametro minimo delle barre longitudinali"),
    ("ca-pilastro-rettangolare", "Interasse massimo delle barre longitudinali"),
    ("ca-pilastro-rettangolare", "Area minima di armatura longitudinale"),
    ("ca-pilastro-rettangolare", "Diametro minimo delle staffe"),
    ("ca-pilastro-rettangolare", "Interasse massimo delle staffe"),
    ("ca-pilastro-circolare", "Percentuale di armatura longitudinale"),
    ("ca-pilastro-circolare", "Verifica di snellezza"),
    ("ca-pilastro-circolare", "Diametro minimo delle barre longitudinali"),
    ("ca-pilastro-circolare", "Interasse massimo delle barre longitudinali"),
    ("ca-pilastro-circolare", "Area minima di armatura longitudinale"),
    ("ca-pilastro-circolare", "Diametro minimo delle staffe"),
    ("ca-pilastro-circolare", "Interasse massimo delle staffe"),
    ("ca-trave-rettangolare", "Passo massimo staffe"),
    ("ca-trave-rettangolare", "Percentuale di armatura tesa minima sismica"),
    ("ca-trave-rettangolare", "Percentuale di armatura tesa massima sismica"),
    ("ca-trave-rettangolare", "Armatura compressa minima sismica"),
    ("ca-trave-rettangolare", "Duttilità sezione (acciaio snervato)"),
    ("ca-trave-rettangolare", "Classe di apertura fessura conforme a Tab. 4.1.IV"),
})


def test_copertura_rapporti_congelata():
    trovate: set[tuple[str, str]] = set()
    for tool in discover().values():
        if tool.example is None:
            continue
        report = execute(tool, tool.example)
        if not report.ok:
            continue
        for check in report.checks:
            if rapporto(check) is None:
                trovate.add((tool.name, check.name))
    assert trovate == _ATTESE_SENZA_RAPPORTO

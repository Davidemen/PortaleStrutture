"""Golden case on `muro-sostegno` (WORKBENCH_SPEC §23.6): a real tool with both demand/capacity and
minimum checks. `h_muro_m` has a clean N…N A…A boundary (larger wall = less stable) in [1.5, 3.5] m
with `passo=0.1` — verified once, by hand, in the worktree before writing this test:
`uv run python -c "..."` at h=2.8 (admissible) and h=2.9 (not) with the tool's own example inputs."""
from decimal import Decimal

from strutture.members.muro.tool import TOOLS as MURO_TOOLS
from strutture.shared.dimensiona.esecuzione import (
    costruisci_valuta,
    esito_alla_risposta,
    impara_da_riporti,
    valutazioni_iniziali,
)
from strutture.shared.dimensiona.griglia import costruisci_griglia
from strutture.shared.dimensiona.ricerca import cerca
from strutture.shared.tool import execute

_MURO = next(t for t in MURO_TOOLS if t.name == "muro-sostegno")


def _cerca_h_muro(obiettivo: float):
    griglia = costruisci_griglia(1.5, 3.5, 0.1, intero=False)
    inputs = _MURO.example
    riporti = valutazioni_iniziali(_MURO, inputs, "h_muro_m", griglia)
    orientamenti = impara_da_riporti(riporti)
    base = riporti[griglia[0]]
    avvisi_base = tuple(base.get("warnings", ()))
    valuta, cache = costruisci_valuta(_MURO, inputs, "h_muro_m", riporti, orientamenti, obiettivo, False, avvisi_base)
    risultato = cerca(griglia, valuta, "massimo")
    return risultato, griglia, inputs, orientamenti, cache


def test_muro_sostegno_h_muro_massimo_ammissibile():
    risultato, _, inputs, _, _ = _cerca_h_muro(1.00)
    assert risultato.esito == "trovato"
    assert risultato.verso == "massimo"
    assert risultato.valore is not None

    v = float(risultato.valore)
    v_meno_passo = float(risultato.valore - Decimal("0.1"))
    ammissibile_v = execute(_MURO, {**inputs, "h_muro_m": v})
    ammissibile_v_meno_passo = execute(_MURO, {**inputs, "h_muro_m": v_meno_passo})
    assert ammissibile_v.ok and all(c.passed for c in ammissibile_v.checks)
    # one step further (larger, less stable) must NOT be admissible: v is the true boundary
    v_piu_passo = float(risultato.valore + Decimal("0.1"))
    oltre = execute(_MURO, {**inputs, "h_muro_m": v_piu_passo})
    assert not (oltre.ok and all(c.passed for c in oltre.checks))
    assert ammissibile_v_meno_passo.ok and all(c.passed for c in ammissibile_v_meno_passo.checks)


def test_muro_sostegno_obiettivo_piu_permissivo_da_valore_maggiore_o_uguale():
    risultato_stretto, *_ = _cerca_h_muro(1.00)
    risultato_permissivo, *_ = _cerca_h_muro(0.80)
    assert risultato_permissivo.valore is not None and risultato_stretto.valore is not None
    assert risultato_permissivo.valore >= risultato_stretto.valore


def test_muro_sostegno_report_alla_risposta_disponibile():
    risultato, _, inputs, orientamenti, cache = _cerca_h_muro(1.00)
    report, esito = esito_alla_risposta(
        risultato.valore, _MURO, inputs, "h_muro_m", cache, orientamenti, 1.00, False,
    )
    assert report is not None and report["ok"]
    assert esito is not None and esito.ammissibile

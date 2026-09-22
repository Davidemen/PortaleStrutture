"""Golden case on `muro-sostegno` (WORKBENCH_SPEC §23.6): a real tool with both demand/capacity and
minimum checks. `h_muro_m` has a clean N…N A…A boundary (larger wall = less stable) in [1.5, 3.5] m
with `passo=0.1` — verified once, by hand, in the worktree before writing this test:
`uv run python -c "..."` at h=2.8 (admissible) and h=2.9 (not) with the tool's own example inputs."""
from decimal import Decimal

import pytest

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


def _cerca_h_muro(obiettivo: float, *, obiettivo_su_minimi: bool = False):
    griglia = costruisci_griglia(1.5, 3.5, 0.1, intero=False)
    inputs = _MURO.example
    riporti = valutazioni_iniziali(_MURO, inputs, "h_muro_m", griglia)
    orientamenti = impara_da_riporti(riporti)
    base = riporti[griglia[0]]
    avvisi_base = tuple(base.get("warnings", ()))
    valuta, cache = costruisci_valuta(
        _MURO, inputs, "h_muro_m", riporti, orientamenti, obiettivo, obiettivo_su_minimi, avvisi_base,
    )
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


def test_muro_sostegno_obiettivo_piu_severo_da_valore_minore_o_uguale():
    """Every check on `muro-sostegno` is "inverso" (η = 1/r, verified once by hand: `impara_da_
    riporti` gives "inverso" for all of them) -- with `obiettivo_su_minimi=False` (the search's
    default) `obiettivo` therefore has NO effect at all on the answer here, so this golden must
    force `obiettivo_su_minimi=True` for the comparison to test anything real. With `verso=
    "massimo"` a SMALLER (stricter) obiettivo caps η lower, which for an increasing-η-with-h
    tool caps the admissible height LOWER too -- v' <= v, not the other way round."""
    risultato_large, *_ = _cerca_h_muro(1.00, obiettivo_su_minimi=True)
    risultato_stretto, *_ = _cerca_h_muro(0.95, obiettivo_su_minimi=True)
    assert risultato_large.valore is not None and risultato_stretto.valore is not None
    assert risultato_stretto.valore <= risultato_large.valore
    assert risultato_stretto.valore < risultato_large.valore  # actually strictly smaller here


def test_muro_sostegno_report_alla_risposta_disponibile():
    risultato, _, inputs, orientamenti, cache = _cerca_h_muro(1.00)
    report, esito = esito_alla_risposta(
        risultato.valore, _MURO, inputs, "h_muro_m", cache, orientamenti, 1.00, False,
    )
    assert report is not None and report["ok"]
    assert esito is not None and esito.ammissibile


def test_muro_sostegno_via_endpoint_post_dimensiona():
    """Same golden, through the real HTTP endpoint (not the pure functions directly) -- catches a
    regression in the route's own wiring (validation, mode forcing, response shape) that the pure
    tests above cannot."""
    from fastapi.testclient import TestClient

    from strutture.web.app import create_app

    client = TestClient(create_app())
    body = {
        "inputs": _MURO.example, "campo": "h_muro_m", "da": 1.5, "a": 3.5, "passo": 0.1,
        "obiettivo": 1.0, "verso": "massimo",
    }
    response = client.post("/api/tools/muro-sostegno/dimensiona", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ok"] is True
    assert data["esito"] == "trovato"
    assert data["valore"] == pytest.approx(2.8)

"""Contract-shaped stub responses for `/api/midas/*` (MIDAS.md §4).

No real MIDAS relay (and, at the time this suite was written, no real backend route either --
DESIGN_SPEC/MIDAS.md task split) is available, so these fixtures ARE the fake relay: Playwright's
`page.route("**/api/midas/**", ...)` fulfils every call at OUR API boundary with exactly the
shapes MIDAS.md §4 documents, and the dialog (js/midas-dialog.js) is exercised against them like
it would be against the real backend.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

STATUS_NO_SERVER_KEY = {"server_key": False, "base_url": None, "product": None}

VERIFY_OK = {
    "ok": True,
    "product": "gen",
    "name": "MIDAS Gen NX",
    "version": "2024 v1.1",
    "base_url": "https://moa-engineers-gb.midasit.com:443/gen",
    "units": {"force": "KN", "dist": "M"},
}

VERIFY_ERROR = {"ok": False, "errors": ["Chiave non valida o scaduta."], "kind": "auth"}

COMBINATIONS_OK = {
    "combinations": [
        {
            "name": "SLU1(CB)",
            "table_name": "SLU1(CB)",
            "classification": "SLU",
            "active": "ACTIVE",
            "description": "Combinazione fondamentale 1",
            "famiglia_suggerita": "SLU_STR",
        },
        {
            "name": "SLE1(CB)",
            "table_name": "SLE1(CB)",
            "classification": "SLE",
            "active": "ACTIVE",
            "description": "Combinazione rara 1",
            "famiglia_suggerita": "SLE_RARA",
        },
        {
            "name": "OLD(CB)",
            "table_name": "OLD(CB)",
            "classification": "SLU",
            "active": "INACTIVE",
            "description": "Combinazione dismessa",
            "famiglia_suggerita": None,
        },
    ]
}

SUPPORTS_OK = {"supports": [{"nodo": n, "x_m": float(n), "y_m": 0.0, "z_m": 0.0} for n in (1, 2, 3)]}

REACTIONS_OK = {
    "righe": [
        {"nodo": 1, "combo": "SLU1", "famiglia": "SLU_STR", "fx_kN": 1.0, "fy_kN": 2.0, "fz_kN": 100.0, "mx_kNm": 0.5, "my_kNm": 0.6, "mz_kNm": 0.0},
        {"nodo": 2, "combo": "SLU1", "famiglia": "SLU_STR", "fx_kN": 1.5, "fy_kN": 2.5, "fz_kN": 150.0, "mx_kNm": 0.7, "my_kNm": 0.8, "mz_kNm": 0.1},
    ],
    "n_righe": 2,
    "avvisi": [],
}


def _fulfil(route: Route, payload: dict, status: int = 200) -> None:
    route.fulfill(status=status, content_type="application/json", body=json.dumps(payload))


def install_happy_path(page: Page) -> None:
    """Route every /api/midas/* call so a full Connessione -> Importa walk succeeds."""

    def handler(route: Route) -> None:
        url = route.request.url
        if url.endswith("/api/midas/status"):
            _fulfil(route, STATUS_NO_SERVER_KEY)
        elif url.endswith("/api/midas/verify"):
            _fulfil(route, VERIFY_OK)
        elif url.endswith("/api/midas/combinations"):
            _fulfil(route, COMBINATIONS_OK)
        elif url.endswith("/api/midas/supports"):
            _fulfil(route, SUPPORTS_OK)
        elif url.endswith("/api/midas/reactions"):
            _fulfil(route, REACTIONS_OK)
        else:
            route.continue_()

    page.route("**/api/midas/**", handler)


def install_verify_error(page: Page) -> None:
    """Route status normally but fail `verify` with a 401 auth error (MIDAS.md §4)."""

    def handler(route: Route) -> None:
        url = route.request.url
        if url.endswith("/api/midas/status"):
            _fulfil(route, STATUS_NO_SERVER_KEY)
        elif url.endswith("/api/midas/verify"):
            _fulfil(route, VERIFY_ERROR, status=401)
        else:
            route.continue_()

    page.route("**/api/midas/**", handler)

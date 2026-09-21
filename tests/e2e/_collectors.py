"""Console-error, CSP-violation and off-origin-request collectors for a Playwright page.

The CSP listener is registered via `add_init_script` so it exists before any app script
runs, per DESIGN_SPEC §7 test 10.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

_CSP_INIT_SCRIPT = """
window.__e2eCsp = [];
document.addEventListener('securitypolicyviolation', (event) => {
  window.__e2eCsp.push(event.violatedDirective + ' :: ' + event.blockedURI);
});
"""


class PageCollectors:
    """Mutable-by-design event sink attached once per page; not shared app state."""

    def __init__(self) -> None:
        self.console_errors: list[str] = []
        self.page_errors: list[str] = []
        self.requests: list[str] = []


def attach(page: Page) -> PageCollectors:
    """Attach listeners to `page` before navigation and return the sink to assert on later."""
    collectors = PageCollectors()
    page.add_init_script(_CSP_INIT_SCRIPT)
    page.on("console", lambda msg: collectors.console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda error: collectors.page_errors.append(str(error)))
    page.on("request", lambda request: collectors.requests.append(request.url))
    return collectors


def csp_violations(page: Page) -> list[str]:
    return page.evaluate("window.__e2eCsp || []")


def off_origin_requests(collectors: PageCollectors, base_url: str) -> list[str]:
    return [url for url in collectors.requests if not url.startswith(base_url) and not url.startswith("data:")]

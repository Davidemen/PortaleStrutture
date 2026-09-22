"""Generic, schema-driven web app factory. No per-tool code lives here."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from strutture.shared.impostazioni.modelli import Impostazioni, ImpostazioniSalvate
from strutture.shared.tool import Tool, discover
from strutture.storage.interfaces import ImpostazioniRepository, ProjectRepository, SignoffRepository
from strutture.storage.models import (
    Elemento,
    Progetto,
    RevisioneElemento,
    Signoff,
    Stato,
)

from . import config
from .middleware.body_limit import BodySizeLimitMiddleware
from .middleware.cache_control import CacheControlMiddleware
from .middleware.rate_limit import SlidingWindowRateLimitMiddleware
from .middleware.same_origin import SameOriginMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .routes.comuni import build_comuni_router
from .routes.dimensiona import StatoDimensiona, build_dimensiona_router
from .routes.divergences import build_divergences_router
from .routes.impostazioni import build_impostazioni_router
from .routes.midas import build_midas_router
from .routes.progetti import build_progetti_router
from .routes.progetti_stato import build_progetti_stato_router
from .routes.tools import build_tools_router


def create_app(
    tools: dict[str, Tool] | None = None,
    settings: config.Settings | None = None,
    signoffs: SignoffRepository | None = None,
    progetti: ProjectRepository | None = None,
    impostazioni: ImpostazioniRepository | None = None,
) -> FastAPI:
    """Build the FastAPI app. `tools` defaults to `discover()`; inject a fake registry for tests.
    `signoffs`/`progetti`/`impostazioni` default to the real SQLite repositories, imported lazily so
    tests never need them (they inject small in-test fakes implementing the respective Protocols
    instead)."""
    resolved_tools = tools if tools is not None else discover()
    resolved_settings = settings if settings is not None else config.from_env()
    resolved_signoffs = signoffs if signoffs is not None else _default_signoff_repository(resolved_settings.data_dir)
    resolved_progetti = progetti if progetti is not None else _default_project_repository(resolved_settings.data_dir)
    resolved_impostazioni = (
        impostazioni if impostazioni is not None else _default_impostazioni_repository(resolved_settings.data_dir)
    )

    app = FastAPI(title="StruttureMenni", docs_url=None, redoc_url=None)

    # Starlette runs the *last*-added middleware outermost, so SecurityHeaders (added last)
    # wraps every response -- including the ones RateLimit/BodySizeLimit/SameOrigin short-circuit.
    # SameOrigin is added right before it, so a CSRF attempt is rejected before it can consume rate
    # limit budget or have its body read.
    app.add_middleware(SlidingWindowRateLimitMiddleware, limit_per_minute=resolved_settings.rate_limit_per_minute)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=resolved_settings.max_body_bytes)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(SameOriginMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.state.dimensiona = StatoDimensiona()
    app.include_router(build_tools_router(resolved_tools))
    app.include_router(build_dimensiona_router(resolved_tools, resolved_signoffs))
    app.include_router(build_comuni_router())
    app.include_router(build_midas_router())
    app.include_router(build_divergences_router(resolved_signoffs))
    app.include_router(build_progetti_router(resolved_progetti, resolved_tools))
    app.include_router(build_impostazioni_router(resolved_impostazioni, resolved_tools))
    app.include_router(build_progetti_stato_router(resolved_progetti, resolved_tools, resolved_signoffs))
    app.mount("/", StaticFiles(directory=resolved_settings.static_dir, html=True), name="static")

    return app


def _default_signoff_repository(data_dir: Path) -> SignoffRepository:
    """Deferred to `_LazySqliteSignoffRepository`: the SQLite module is written by another agent
    in parallel, so it must not be imported before the first real call reaches it — otherwise every
    test that builds an app without passing `signoffs` (unrelated tool/comuni/midas tests) would
    fail while that module does not exist yet."""
    return _LazySqliteSignoffRepository(data_dir)


class _LazySqliteSignoffRepository:
    """Implements `SignoffRepository`, importing and opening the real repository on first use."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._repository: SignoffRepository | None = None

    def _resolved(self) -> SignoffRepository:
        if self._repository is None:
            from strutture.storage.signoff_sqlite import open_signoff_repository

            self._repository = open_signoff_repository(self._data_dir)
        return self._repository

    def get(self, divergence_id: str) -> Signoff:
        return self._resolved().get(divergence_id)

    def list_all(self) -> dict[str, Signoff]:
        return self._resolved().list_all()

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        return self._resolved().set(divergence_id, stato, sigla, nota)

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        return self._resolved().history(divergence_id)


def _default_project_repository(data_dir: Path) -> ProjectRepository:
    """Deferred to `_LazySqliteProjectRepository`: `progetti_sqlite` is written by another agent
    in parallel, so it must not be imported before the first real call reaches it — otherwise every
    test that builds an app without passing `progetti` (unrelated tool/comuni/midas tests) would
    fail while that module does not exist yet."""
    return _LazySqliteProjectRepository(data_dir)


class _LazySqliteProjectRepository:
    """Implements `ProjectRepository`, importing and opening the real repository on first use."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._repository: ProjectRepository | None = None

    def _resolved(self) -> ProjectRepository:
        if self._repository is None:
            from strutture.storage.progetti_sqlite import open_project_repository

            self._repository = open_project_repository(self._data_dir)
        return self._repository

    def list_progetti(self, *, inclusi_eliminati: bool = False) -> tuple[Progetto, ...]:
        return self._resolved().list_progetti(inclusi_eliminati=inclusi_eliminati)

    def get_progetto(self, progetto_id: str) -> Progetto:
        return self._resolved().get_progetto(progetto_id)

    def crea_progetto(self, progetto: Progetto) -> Progetto:
        return self._resolved().crea_progetto(progetto)

    def aggiorna_progetto(self, progetto: Progetto) -> Progetto:
        return self._resolved().aggiorna_progetto(progetto)

    def elimina_progetto(self, progetto_id: str, revisione: int) -> None:
        self._resolved().elimina_progetto(progetto_id, revisione)

    def ripristina_progetto(self, progetto_id: str) -> Progetto:
        return self._resolved().ripristina_progetto(progetto_id)

    def list_elementi(self, progetto_id: str, *, inclusi_eliminati: bool = False) -> tuple[Elemento, ...]:
        return self._resolved().list_elementi(progetto_id, inclusi_eliminati=inclusi_eliminati)

    def get_elemento(self, elemento_id: str) -> Elemento:
        return self._resolved().get_elemento(elemento_id)

    def crea_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        return self._resolved().crea_elemento(elemento, sigla=sigla, nota=nota)

    def aggiorna_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        return self._resolved().aggiorna_elemento(elemento, sigla=sigla, nota=nota)

    def duplica_elemento(self, elemento_id: str, nuovo_nome: str) -> Elemento:
        return self._resolved().duplica_elemento(elemento_id, nuovo_nome)

    def elimina_elemento(self, elemento_id: str, revisione: int) -> None:
        self._resolved().elimina_elemento(elemento_id, revisione)

    def ripristina_elemento(self, elemento_id: str) -> Elemento:
        return self._resolved().ripristina_elemento(elemento_id)

    def revisioni(self, elemento_id: str) -> tuple[RevisioneElemento, ...]:
        return self._resolved().revisioni(elemento_id)


def _default_impostazioni_repository(data_dir: Path) -> ImpostazioniRepository:
    """Deferred to `_LazySqliteImpostazioniRepository`, same reasoning as the other two lazy
    repositories above: the SQLite module must not be imported before the first real call."""
    return _LazySqliteImpostazioniRepository(data_dir)


class _LazySqliteImpostazioniRepository:
    """Implements `ImpostazioniRepository`, importing and opening the real repository on first use."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._repository: ImpostazioniRepository | None = None

    def _resolved(self) -> ImpostazioniRepository:
        if self._repository is None:
            from strutture.storage.impostazioni_sqlite import open_impostazioni_repository

            self._repository = open_impostazioni_repository(self._data_dir)
        return self._repository

    def leggi(self) -> ImpostazioniSalvate:
        return self._resolved().leggi()

    def salva(self, valori: Impostazioni, revisione_attesa: int, sigla: str) -> ImpostazioniSalvate:
        return self._resolved().salva(valori, revisione_attesa, sigla)

    def storia(self, limite: int = 50) -> tuple[ImpostazioniSalvate, ...]:
        return self._resolved().storia(limite)

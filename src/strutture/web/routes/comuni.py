"""API route backing the searchable comune dropdown."""
from typing import Annotated

from fastapi import APIRouter, Query

from strutture.shared.comuni import search_options

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 60
DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def build_comuni_router() -> APIRouter:
    router = APIRouter(prefix="/api/comuni")

    @router.get("")
    def search(
        q: Annotated[str, Query(min_length=MIN_QUERY_LENGTH, max_length=MAX_QUERY_LENGTH)],
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    ) -> list[dict[str, str]]:
        """Comuni whose name starts with `q`; `label` is what the tools accept as `comune`."""
        return [
            {
                "label": option.label,
                "comune": option.comune.comune,
                "provincia": option.comune.provincia,
                "regione": option.comune.regione,
            }
            for option in search_options(q, limit)
        ]

    return router

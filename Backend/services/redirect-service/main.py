from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import RedirectResponse
from typing import Annotated
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from redirect_lookup_service import (
    RedirectDependencyError,
    RedirectLookupError,
    RedirectNotFoundError,
    resolve_original_url,
    resolve_with_metadata,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResolveResponse(BaseModel):
    short_code: str
    original_url: str
    source: str  
    server_latency_ms: float


@app.get('/resolve/{short_code}', response_model=ResolveResponse)
def resolve_short_code(short_code: Annotated[str, Path()]) -> ResolveResponse:
    """
    Resolve a short code to original URL with metadata.
    Returns cache/db source and server latency for analytics.
    """
    try:
        original_url, source, server_latency_ms = resolve_with_metadata(short_code)
    except RedirectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RedirectDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except RedirectLookupError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ResolveResponse(
        short_code=short_code,
        original_url=original_url,
        source=source,
        server_latency_ms=server_latency_ms,
    )


@app.get('/{short_code}')
def redirect_to_original(short_code: Annotated[str, Path()]):
    try:
        original_url = resolve_original_url(short_code)
    except RedirectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RedirectDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except RedirectLookupError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return RedirectResponse(url=original_url, status_code=302)
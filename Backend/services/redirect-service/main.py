from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import RedirectResponse
from typing import Annotated

from redirect_lookup_service import (
    RedirectDependencyError,
    RedirectLookupError,
    RedirectNotFoundError,
    resolve_original_url,
)

app = FastAPI()


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
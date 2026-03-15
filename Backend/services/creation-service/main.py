from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from short_url_creation_service import (
    CreationDependencyError,
    CreationError,
    CreationPersistError,
    create_short_url_mapping,
)

app = FastAPI()


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_url: str
    original_url: str


@app.post('/create', response_model=ShortenResponse, status_code=201)
def create_short_url(body: ShortenRequest) -> ShortenResponse:
    original_url = str(body.url)

    try:
        short_url, original_url = create_short_url_mapping(original_url)
    except CreationDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except CreationPersistError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except CreationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ShortenResponse(short_url=short_url, original_url=original_url)




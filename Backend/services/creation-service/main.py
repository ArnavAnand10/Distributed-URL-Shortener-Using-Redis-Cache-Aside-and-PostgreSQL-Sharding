from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
from short_url_creation_service import (
    CreationDependencyError,
    CreationError,
    CreationPersistError,
    create_short_url_mapping,
)
from postgres_repository import apply_schema_to_all_shards
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Apply schema to all shards
    print("Initializing database schema...")
    try:
        apply_schema_to_all_shards()
        print("Database schema initialized successfully")
    except Exception as exc:
        print(f"Warning: Failed to initialize schema: {exc}")
    yield
    # Shutdown: Add any cleanup here if needed


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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




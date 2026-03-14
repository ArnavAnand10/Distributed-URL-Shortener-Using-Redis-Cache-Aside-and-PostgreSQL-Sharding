from fastapi import FastAPI, HTTPException
from short_url_generator import short_url_generator
from pydantic import BaseModel, HttpUrl
import config
from redis.exceptions import RedisError
from postgres_repository import (
    DataWriteError,
    DatabaseUnavailableError,
    save_mapping,
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
        short_url = short_url_generator()
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error while generating short URL")

    try:
        save_mapping(short_url, original_url)
    except DatabaseUnavailableError:
        raise HTTPException(status_code=503, detail="PostgreSQL service unavailable")
    except DataWriteError:
        raise HTTPException(status_code=500, detail="Failed to persist short URL")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Cache write is best effort because PostgreSQL is the source of truth.
    try:
        config.redis_client.set(f"url:{short_url}", original_url)
    except RedisError:
        pass
    except Exception:
        pass

    return ShortenResponse(short_url=short_url, original_url=original_url)




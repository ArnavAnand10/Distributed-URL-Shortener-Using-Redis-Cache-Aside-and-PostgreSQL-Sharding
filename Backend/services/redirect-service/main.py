from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
import config

app = FastAPI



@app.get('/redirect/{short_code}')
def redirect_to_original(short_code: str):
    try:
        original_url = config.redis_client.get(f"url:{short_code}")
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during redirect lookup")

    if not original_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return RedirectResponse(url=original_url, status_code=302)
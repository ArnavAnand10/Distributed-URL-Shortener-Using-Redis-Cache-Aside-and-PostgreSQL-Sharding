from redis.exceptions import RedisError

import config
from postgres_repository import DatabaseUnavailableError, DataReadError, get_mapping


class RedirectLookupError(Exception):
    pass


class RedirectDependencyError(Exception):
    pass


class RedirectNotFoundError(Exception):
    pass


def resolve_original_url(short_code: str) -> str:
    original_url = None

    try:
        original_url = config.redis_client.get(f"url:{short_code}")
    except (RedisError, Exception):
        original_url = None

    if original_url:
        return original_url

    try:
        original_url = get_mapping(short_code)
    except DatabaseUnavailableError as exc:
        raise RedirectDependencyError("PostgreSQL service unavailable") from exc
    except DataReadError as exc:
        raise RedirectLookupError("Failed to fetch URL mapping") from exc
    except Exception as exc:
        raise RedirectLookupError("Unexpected error during redirect lookup") from exc

    if not original_url:
        raise RedirectNotFoundError("Original URL not found for this short URL")

    try:
        config.redis_client.set(f"url:{short_code}", original_url)
    except (RedisError, Exception):
        pass

    return original_url
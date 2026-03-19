from redis.exceptions import RedisError
import time
from typing import Tuple
import logging

import config
from postgres_repository import DatabaseUnavailableError, DataReadError, get_mapping


logger = logging.getLogger(__name__)


class RedirectLookupError(Exception):
    pass


class RedirectDependencyError(Exception):
    pass


class RedirectNotFoundError(Exception):
    pass


def resolve_original_url(short_code: str) -> str:
    logger.info(f"Resolving {short_code}")
    original_url = None

    try:
        original_url = config.redis_client.get(f"url:{short_code}")
    except (RedisError, Exception):
        original_url = None

    if original_url:
        logger.info(f"{short_code}: cache hit")
        return original_url

    logger.info(f"{short_code}: cache miss, querying DB")
    try:
        original_url = get_mapping(short_code)
    except DatabaseUnavailableError as exc:
        logger.error(f"{short_code}: Database unavailable: {exc}")
        raise RedirectDependencyError("PostgreSQL service unavailable") from exc
    except DataReadError as exc:
        logger.error(f"{short_code}: Data read error: {exc}")
        raise RedirectLookupError("Failed to fetch URL mapping") from exc
    except Exception as exc:
        logger.error(f"{short_code}: Unexpected error: {exc}")
        raise RedirectLookupError("Unexpected error during redirect lookup") from exc

    if not original_url:
        logger.warning(f"{short_code}: Not found in database")
        raise RedirectNotFoundError("Original URL not found for this short URL")

    try:
        config.redis_client.set(f"url:{short_code}", original_url)
    except (RedisError, Exception):
        pass

    logger.info(f"{short_code}: DB hit, cached")
    return original_url


def resolve_with_metadata(short_code: str) -> Tuple[str, str, int]:
  
    start_time = time.time()
    original_url = None
    source = None

    try:
        original_url = config.redis_client.get(f"url:{short_code}")
        if original_url:
            source = "cache"
    except (RedisError, Exception):
        original_url = None

    if not original_url:
        try:
            original_url = get_mapping(short_code)
            source = "db"
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

    end_time = time.time()
    server_latency_ms = round((end_time - start_time) * 1000, 1)

    return original_url, source, server_latency_ms
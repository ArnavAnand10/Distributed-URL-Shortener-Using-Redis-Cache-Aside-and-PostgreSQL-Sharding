from redis.exceptions import RedisError

import config
from postgres_repository import DataWriteError, DatabaseUnavailableError, save_mapping
from short_url_generator import short_url_generator


class CreationError(Exception):
    pass


class CreationDependencyError(CreationError):
    pass


class CreationPersistError(CreationError):
    pass


def create_short_url_mapping(original_url: str) -> tuple[str, str]:
    try:
        short_url = short_url_generator()
    except RedisError as exc:
        raise CreationDependencyError("Redis service unavailable") from exc
    except Exception as exc:
        raise CreationError("Unexpected error while generating short URL") from exc

    try:
        save_mapping(short_url, original_url)
    except DatabaseUnavailableError as exc:
        raise CreationDependencyError("PostgreSQL service unavailable") from exc
    except DataWriteError as exc:
        raise CreationPersistError("Failed to persist short URL") from exc
    except ValueError as exc:
        raise CreationError(str(exc)) from exc

    

    return short_url, original_url
from typing import Optional

import psycopg
from psycopg.errors import Error as PsycopgError

import config


class RepositoryError(Exception):
    pass


class DatabaseUnavailableError(RepositoryError):
    pass


class DataWriteError(RepositoryError):
    pass


class DataReadError(RepositoryError):
    pass


def _get_connection() -> psycopg.Connection:
    dsn = config.get_current_shard_dsn()

    try:
        return psycopg.connect(dsn, connect_timeout=3)
    except PsycopgError as exc:
        raise DatabaseUnavailableError("PostgreSQL connection failed") from exc


def save_mapping(short_code: str, original_url: str) -> None:
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO url_mappings (short_code, original_url)
                    VALUES (%s, %s)
                    ON CONFLICT (short_code)
                    DO UPDATE SET original_url = EXCLUDED.original_url
                    """,
                    (short_code, original_url),
                )
    except DatabaseUnavailableError:
        raise
    except PsycopgError as exc:
        raise DataWriteError("Failed to save URL mapping") from exc


def get_mapping(short_code: str) -> Optional[str]:
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT original_url FROM url_mappings WHERE short_code = %s",
                    (short_code,),
                )
                row = cur.fetchone()
    except DatabaseUnavailableError:
        raise
    except PsycopgError as exc:
        raise DataReadError("Failed to fetch URL mapping") from exc

    if row is None:
        return None

    return row[0]

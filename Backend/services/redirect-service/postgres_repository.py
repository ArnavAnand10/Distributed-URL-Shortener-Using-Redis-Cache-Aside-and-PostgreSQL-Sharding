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


def _get_connection(dsn : str) -> psycopg.Connection:

    try:
        return psycopg.connect(dsn, connect_timeout=3)
    except PsycopgError as exc:
        raise DatabaseUnavailableError("PostgreSQL connection failed") from exc




def get_mapping(short_code: str) -> Optional[str]:
    dsn = config.get_shard_dsn_for_short_code(short_code)
    try:
        with _get_connection(dsn) as conn:
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

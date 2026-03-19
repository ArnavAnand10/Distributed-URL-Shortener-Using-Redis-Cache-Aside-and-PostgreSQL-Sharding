from typing import Optional
import logging

import psycopg
from psycopg.errors import Error as PsycopgError

import config


logger = logging.getLogger(__name__)


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
        logger.debug(f"Connecting to: {dsn}")
        return psycopg.connect(dsn, connect_timeout=3)
    except PsycopgError as exc:
        logger.error(f"Connection failed: {exc}")
        raise DatabaseUnavailableError("PostgreSQL connection failed") from exc




def get_mapping(short_code: str) -> Optional[str]:
    dsn = config.get_shard_dsn_for_short_code(short_code)
    logger.info(f"Querying {short_code} from shard DSN ending in: ...{dsn[-30:]}")
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
        logger.error(f"Query failed for {short_code}: {exc}")
        raise DataReadError("Failed to fetch URL mapping") from exc

    if row is None:
        logger.warning(f"{short_code} not found in database")
        return None

    logger.info(f"{short_code} found: {row[0][:50]}...")
    return row[0]

from typing import Optional
from pathlib import Path

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


def _get_connection_to_shard(dsn: str) -> psycopg.Connection:
    """Get connection to a specific shard by DSN."""
    try:
        return psycopg.connect(dsn, connect_timeout=3)
    except PsycopgError as exc:
        raise DatabaseUnavailableError("PostgreSQL connection failed") from exc


def apply_schema_to_all_shards() -> None:
    """Apply the schema to all PostgreSQL shards."""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text()

    shards = [
        ("SHARD_0", config.SHARD_0_DSN),
        ("SHARD_1", config.SHARD_1_DSN),
        ("SHARD_2", config.SHARD_2_DSN),
    ]

    for shard_name, dsn in shards:
        if not dsn:
            print(f"{shard_name}: DSN not configured, skipping")
            continue

        try:
            with _get_connection_to_shard(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            print(f"{shard_name}: schema applied successfully")
        except DatabaseUnavailableError as exc:
            print(f"{shard_name}: connection failed -> {exc}")
        except PsycopgError as exc:
            print(f"{shard_name}: schema application failed -> {exc}")
        except Exception as exc:
            print(f"{shard_name}: unexpected error -> {exc}")


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

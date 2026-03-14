from pathlib import Path

import psycopg


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("\"'")
    return env


def main() -> None:
    env_path = Path("d:/URL Shortener/Backend/services/creation-service/.env")
    schema_path = Path("d:/URL Shortener/Backend/services/creation-service/schema.sql")

    env = load_env(env_path)
    schema_sql = schema_path.read_text()

    for shard_key in ("SHARD_0_DSN", "SHARD_1_DSN", "SHARD_2_DSN"):
        dsn = env.get(shard_key, "")
        if not dsn:
            print(f"{shard_key}: missing")
            continue

        try:
            with psycopg.connect(dsn, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            print(f"{shard_key}: schema applied")
        except Exception as exc:
            print(f"{shard_key}: failed -> {exc}")


if __name__ == "__main__":
    main()

import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  
)



SHARD_0_DSN = os.getenv("SHARD_0_DSN", "")
SHARD_1_DSN = os.getenv("SHARD_1_DSN", "")
SHARD_2_DSN = os.getenv("SHARD_2_DSN", "")

MACHINE_TO_SHARD = {
    "a": 0,
    "b": 1,
    "c": 2,
}

SHARD_DSN_MAP = {
    0: SHARD_0_DSN,
    1: SHARD_1_DSN,
    2: SHARD_2_DSN,
}


def get_shard_dsn_for_machine(machine_id: str) -> str:
    normalized_machine_id = machine_id.lower().strip()

    if normalized_machine_id not in MACHINE_TO_SHARD:
        raise ValueError(f"Invalid machine_id '{machine_id}'. Expected one of: a, b, c")

    shard_index = MACHINE_TO_SHARD[normalized_machine_id]
    dsn = SHARD_DSN_MAP.get(shard_index, "")

    if not dsn:
        raise ValueError(f"Missing DSN configuration for shard {shard_index}")

    return dsn


def get_shard_dsn_for_short_code(short_code : str) -> str:
    # extract the machine prefix and then determine the shard access dsn
    if not short_code:
        raise ValueError("Short code cannot be empty")  
    machine_prefix = short_code.lower()[0]
    return get_shard_dsn_for_machine(machine_prefix)

   




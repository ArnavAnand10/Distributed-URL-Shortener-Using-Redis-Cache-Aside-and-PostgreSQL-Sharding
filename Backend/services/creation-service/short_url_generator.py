
from base62_encoding import base62_encode
import config

def short_url_generator()-> str :
    machine_prefix = config.MACHINE_PREFIX
    sequence_number = config.redis_client.incr(config.SEQUENCE_KEY)

    encoded_sequence = base62_encode(sequence_number)
    return machine_prefix+encoded_sequence


if(__name__=='__main__'):
    print(short_url_generator())

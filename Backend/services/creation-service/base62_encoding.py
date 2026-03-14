
"""
Base62 encoding/decoding utilities for URL shortener.
Converts numeric IDs to short alphanumeric strings.
"""

# Base62 alphabet: 0-9, A-Z, a-z (62 characters)
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)  # 62


def base62_encode(num: int) -> str:
    """
    Encode a number to Base62 string.
    
    Args:
        num: Integer to encode (e.g., 123456)
    
    Returns:
        Base62 encoded string (e.g., "w7e")
    """
    if num == 0:
        return ALPHABET[0]
    
    encoded = ""
    while num > 0:
        num, remainder = divmod(num, BASE)
        encoded = ALPHABET[remainder] + encoded
    
    return encoded


def base62_decode(short_code: str) -> int:
    """
    Decode a Base62 string back to number.
    
    Args:
        short_code: Base62 encoded string (e.g., "w7e")
    
    Returns:
        Decoded integer (e.g., 123456)
    """
    num = 0
    for char in short_code:
        value = ALPHABET.index(char)
        num = num * BASE + value
    
    return num


if __name__ == "__main__":
    test_id = 123456
    encoded = base62_encode(test_id)
    decoded = base62_decode(encoded)
    
    print(f"Original ID: {test_id}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Match: {test_id == decoded}")



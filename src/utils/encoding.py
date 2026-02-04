import string

# Shuffled Base 52 (No vowels: a, e, i, o, u, A, E, I, O, U)
CHARSET = "N2Z7P9K6R3V8T4BX5W1GYQSDFHJLMC0bgjknpqrstvwxyzHJKMNPQRSTVWXYZ"
BASE = len(CHARSET)

# Offset for 6-character minimum (52^5 = 380,204,032)
MIN_LENGTH_OFFSET = BASE**5 

def encode_ids(num: int) -> str:
    internal_num = num + MIN_LENGTH_OFFSET
    arr = []
    while internal_num > 0:
        internal_num, rem = divmod(internal_num, BASE)
        arr.append(CHARSET[rem])
    return ''.join(reversed(arr))

def decode_ids(s: str) -> int:
    num = 0
    for i, char in enumerate(reversed(s)):
        num += CHARSET.index(char) * (BASE ** i)
    return num - MIN_LENGTH_OFFSET
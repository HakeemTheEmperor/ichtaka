import string

# Characters for Base62: 0-9, a-z, A-Z
CHARSET = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode_base62(num: int) -> str:
    """Encodes a positive integer to a Base62 string."""
    if num == 0:
        return CHARSET[0]
    
    arr = []
    base = len(CHARSET)
    while num:
        num, rem = divmod(num, base)
        arr.append(CHARSET[rem])
    arr.reverse()
    return ''.join(arr)

def decode_base62(s: str) -> int:
    """Decodes a Base62 string to a positive integer."""
    base = len(CHARSET)
    strlen = len(s)
    num = 0
    
    idx = 0
    for char in s:
        power = (strlen - (idx + 1))
        num += CHARSET.index(char) * (base ** power)
        idx += 1
    return num

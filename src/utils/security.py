import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16
)

def hash_secret(secret: str) -> str:
    return ph.hash(secret)

def verify_secret(secret: str, hashed: str)-> bool:
    try:
        return ph.verify(hashed, secret)
    except VerifyMismatchError:
        return False

def generate_login_id()-> str:
    return "u_" + secrets.token_hex(8)

def generate_pseudonym() -> str:
    adjectives = ["quiet", "blue", "swift", "hidden", "silent"]
    animals = ["otter", "fox", "hawk", "cat", "crow"]
    return f"{secrets.choice(adjectives)}-{secrets.choice(animals)}-{secrets.randbelow(100)}"
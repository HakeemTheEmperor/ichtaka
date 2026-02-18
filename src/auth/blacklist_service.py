from typing import Set
import time
import jwt
from src.config import settings

class TokenBlacklist:
    def __init__(self):
        # In a production environment, use Redis for this.
        # Format: { (token_hash, expiry_timestamp), ... }
        self.blacklisted_tokens: Set[str] = set()

    def add(self, token: str):
        # We can just store the token or its hash.
        # To keep memory low, we should only store until the token's original expiry.
        self.blacklisted_tokens.add(token)

    def is_blacklisted(self, token: str) -> bool:
        return token in self.blacklisted_tokens

    def cleanup(self):
        # Periodically remove expired tokens from the set
        # For simplicity in this MVP, we won't implement full cleanup here
        pass

blacklist = TokenBlacklist()

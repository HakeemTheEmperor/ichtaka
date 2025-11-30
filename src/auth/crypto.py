import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def verify_ed25519_signature(public_key_str:str, message:str, signature_b64:str) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_str))
        signature = base64.b64decode(signature_b64)
        pub.verify(signature, message.encode())
        return True
    except Exception:
        return False    
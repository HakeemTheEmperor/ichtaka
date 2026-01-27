from pydantic import BaseModel, Field, conlist
from typing import Annotated, List
RecoveryPhraseHashes = Annotated[
    List[str],
    Field(
        min_length=20,
        max_length=20,
        description=(
            "Hashed recovery phrase words generated on the client. "
            "The original phrase is never sent to the server."
        )
    )
]

# REQUESTS
class SignupRequest(BaseModel):
    pseudonym: str = Field(description="The user's anonymous identifier", min_length=3)
    public_key: str = Field(description="The Ed25519 public key in base64 format")
    recovery_phrase_hashes: RecoveryPhraseHashes

class LoginRequest(BaseModel):
    pseudonym: str = Field(description="The User's pseudonym")

class VerifyRequest(BaseModel):
    pseudonym: str = Field(description="The User's pseudonym")
    signature: str = Field(description="The Ed25519 signature of the challenge in base64 format")


# RESPONSES
class SignUpResponse(BaseModel):
    id: int
    pseudonym: str
    challenge: str

class LoginResponse(BaseModel):
    pseudonym: str
    challenge: str

class VerifyResponse(BaseModel):
    user_id: int
    token: str

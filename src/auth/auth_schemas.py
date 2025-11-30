from pydantic import BaseModel, Field

# REQUESTS
class SignupRequest(BaseModel):
    public_key: str = Field(description="The user's generated Public Key in PEM format.")
    user_name: str = Field(description="The User's pseudonym. Do not use your real name or anything that can be linked back to you")
    key_algorithm: str = Field(description="The user's key algorithm")

class LoginRequest(BaseModel):
    user_name: str = Field(description="The User's pseudonym, used for Sign up")

class VerifyRequest(BaseModel):
    user_name: str = Field(description="The User's pseudonym, used for Sign up")
    signature: str = Field(description="The signed challenge")


# RESPONSES
class SignUpResponse(BaseModel):
    id: int
    user_name: str
    challenge: str

class LoginResponse(BaseModel):
    user_name: str
    challenge: str

class VerifyResponse(BaseModel):
    user_id: int
    token: str

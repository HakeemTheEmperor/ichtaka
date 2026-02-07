from fastapi import APIRouter,  status
from sqlalchemy.orm import Session
from .auth_schemas import SignupRequest, SignUpResponse,VerifyRequest, VerifyResponse, LoginRequest, LoginResponse, RefreshTokenRequest
from . import auth_service
from .auth_dependencies import DB_SESSION, CURRENT_USER
from src.core.schemas import APIResponse

router = APIRouter()

@router.get("/check-username", response_model=APIResponse[bool], description="Check if a pseudonym is already in use", name='Pseudonym Check')
async def check_username(pseudonym: str, db: DB_SESSION):
    return auth_service.check_username(db, pseudonym)

@router.post("/signup", response_model=APIResponse[SignUpResponse], description="Sign up for first time users", name="Sign up to Ichtaka")
async def signup(data: SignupRequest, db: DB_SESSION):
    return auth_service.signup( db, data=data)

@router.post("/login", response_model=APIResponse[LoginResponse], description="Login to the platform", name="Login")
async def login(data: LoginRequest, db: DB_SESSION):
    return auth_service.login(db, data=data)

@router.post("/verify", response_model=APIResponse[VerifyResponse], description='Verification. After signup/login', name="Verify Identity")
async def verifyAuth(data: VerifyRequest, db: DB_SESSION):
    return auth_service.verify_auth(db, data=data)

@router.post("/refresh", response_model=APIResponse[dict], description="Refresh access token using refresh token", name="Refresh Token")
async def refreshToken(data: RefreshTokenRequest, db: DB_SESSION):
    return auth_service.refresh_access_token(db, refresh_token=data.refresh_token)

@router.post("/logout", response_model=APIResponse[None], description="Logout user and invalidate refresh token", name="Logout")
async def logout(data: RefreshTokenRequest, db: DB_SESSION):
    return auth_service.logout(db, refresh_token=data.refresh_token)
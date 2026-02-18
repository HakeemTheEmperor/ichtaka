from typing import Any, Optional
from fastapi import APIRouter, status, Depends, Request, Response
from .auth_dependencies import DB_SESSION, CURRENT_USER, get_current_user, HTTPAuthorizationCredentials, security, get_optional_current_user
from .import auth_service as service, auth_schemas as schemas
from .models import User_Account
from src.core.schemas import APIResponse

router = APIRouter()

@router.get("/users/{pseudonym}", response_model=APIResponse[Any])
async def get_user_profile(
    pseudonym: str,
    db: DB_SESSION,
    user: Optional[User_Account] = Depends(get_optional_current_user)
):
    return service.get_user_profile(db, pseudonym, user)

@router.get("/check-username", response_model=APIResponse[bool], description="Check if a pseudonym is already in use", name='Pseudonym Check')
async def check_username(pseudonym: str, db: DB_SESSION):
    return service.check_username(db, pseudonym)

@router.post("/signup", response_model=APIResponse[schemas.SignUpResponse], description="Sign up for first time users", name="Sign up to Ichtaka")
async def signup(data: schemas.SignupRequest, db: DB_SESSION):
    return service.signup(db, data=data)

@router.post("/login", response_model=APIResponse[schemas.LoginResponse], description="Login to the platform", name="Login")
async def login(data: schemas.LoginRequest, db: DB_SESSION):
    return service.login(db, data=data)

@router.post("/verify", response_model=APIResponse[schemas.VerifyResponse], description='Verification. After signup/login', name="Verify Identity")
async def verifyAuth(data: schemas.VerifyRequest, db: DB_SESSION, response: Response):
    return service.verify_auth(db, data=data, response=response)

@router.post("/refresh", response_model=APIResponse[dict], description="Refresh access token using refresh token", name="Refresh Token")
async def refreshToken(db: DB_SESSION, request: Request, response: Response, data: Optional[schemas.RefreshTokenRequest] = None):
    refresh_token = data.refresh_token if data else request.cookies.get("refresh_token")
    return service.refresh_access_token(db, refresh_token=refresh_token, response=response)

@router.post("/logout", response_model=APIResponse[None], description="Logout user and invalidate refresh token", name="Logout")
async def logout(db: DB_SESSION, request: Request, response: Response, data: Optional[schemas.RefreshTokenRequest] = None, auth: HTTPAuthorizationCredentials = Depends(security)):
    refresh_token = data.refresh_token if data else request.cookies.get("refresh_token")
    return service.logout(db, refresh_token=refresh_token, access_token=auth.credentials, response=response)

@router.post("/{pseudonym}/follow", response_model=APIResponse[Any])
async def toggle_follow(
    pseudonym: str,
    db: DB_SESSION,
    user: CURRENT_USER
):
    return service.toggle_follow(db, user, pseudonym)

@router.get("/{pseudonym}/followers", response_model=APIResponse[list[schemas.UserListResponse]])
async def get_followers(
    pseudonym: str,
    db: DB_SESSION,
    user: Optional[User_Account] = Depends(get_current_user)
):
    return service.get_followers(db, pseudonym, user)

@router.get("/{pseudonym}/following", response_model=APIResponse[list[schemas.UserListResponse]])
async def get_following(
    pseudonym: str,
    db: DB_SESSION,
    user: Optional[User_Account] = Depends(get_current_user)
):
    return service.get_following(db, pseudonym, user)
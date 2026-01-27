import secrets
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import status
from .models import User_Account
from .auth_schemas import SignupRequest, SignUpResponse, VerifyRequest, VerifyResponse, LoginRequest, LoginResponse
from src.config import settings
from src.core.errors.exceptions import (AlreadyExists, NotFound, InvalidSignature)
from src.core.utils.response import SuccessResponse
from src.auth.crypto import verify_ed25519_signature

JWT_SECRET = settings.JWT_SECRET_KEY
JWT_ALG = settings.JWT_ALGORITHM
JWT_EXP_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def generate_login_id():
    return f"user_{secrets.token_hex(8)}"

def signup(db: Session, data: SignupRequest):
    existing_pseudonym = db.query(User_Account).filter(User_Account.pseudonym == data.pseudonym).first()
    if existing_pseudonym:
        raise AlreadyExists("This pseudonym is already in use")
    
    login_id = generate_login_id()
    challenge = secrets.token_urlsafe(32)
    
    new_user = User_Account(
        login_id=login_id,
        public_key=data.public_key,
        pseudonym=data.pseudonym,
        recovery_phrase_hashes=data.recovery_phrase_hashes,
        current_challenge=challenge
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SuccessResponse(
        message="Signup successful. Verify the challenge to complete registration.", 
        code=status.HTTP_201_CREATED, 
        data=SignUpResponse(
            id=new_user.id, 
            pseudonym=new_user.pseudonym,
            challenge=challenge
        )
    )

def login(db: Session, data: LoginRequest):
    user = db.query(User_Account).filter(User_Account.pseudonym == data.pseudonym).first()
    if not user:
        raise NotFound("User not found.")
    
    challenge = secrets.token_urlsafe(32)
    user.current_challenge = challenge
    db.add(user)
    db.commit()
    
    return SuccessResponse(
        message="Challenge generated. Please sign it with your private key.",
        code=status.HTTP_200_OK,
        data=LoginResponse(
            pseudonym=user.pseudonym,
            challenge=challenge
        )
    )

def check_username(db: Session, user_name: str):
    user = db.query(User_Account).filter(User_Account.pseudonym == user_name).first()
    
    if user:
        raise AlreadyExists('The pseudonym is already in use')
    return SuccessResponse(message="Pseudonym available", code=200, data={"is_available": True})

def verify_auth(db: Session, data: VerifyRequest):
    user = db.query(User_Account).filter(User_Account.pseudonym == data.pseudonym).first()
    if not user:
        raise NotFound('This user account does not exist.')
    
    if not user.current_challenge:
        raise InvalidSignature("No active challenge: try logging in.")
    
    ok = verify_ed25519_signature(user.public_key, user.current_challenge, signature_b64=data.signature)
    if not ok:
        user.current_challenge = None
        db.add(user)
        db.commit()
        raise InvalidSignature('Authentication Failed')
    
    payload = {
        "sub": str(user.id),
        "pseudonym": user.pseudonym,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    
    user.current_challenge = None
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return SuccessResponse(
        message="Authentication successful.", 
        code=status.HTTP_200_OK, 
        data=VerifyResponse(user_id=user.id, token=token)
    )
    
    
    
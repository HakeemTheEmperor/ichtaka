from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session
from src.config import settings
from src.auth.models.user_account import User_Account
from src.database import get_db
from typing import Annotated, Optional

security = HTTPBearer()
DB_SESSION = Annotated[Session, Depends(get_db)]

def get_current_user(
    db: DB_SESSION,
    auth: HTTPAuthorizationCredentials = Depends(security)
) -> User_Account:
    try:
        payload = jwt.decode(
            auth.credentials, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User_Account).filter(User_Account.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except jwt.PyJWTError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

CURRENT_USER = Annotated[User_Account, Depends(get_current_user)]

optional_security = HTTPBearer(auto_error=False)

def get_optional_current_user(
    db: DB_SESSION,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[User_Account]:
    if not auth:
        return None
    try:
        payload = jwt.decode(
            auth.credentials, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User_Account).filter(User_Account.id == int(user_id)).first()
        return user
    except jwt.PyJWTError:
        return None

OPTIONAL_CURRENT_USER = Annotated[Optional[User_Account], Depends(get_optional_current_user)]
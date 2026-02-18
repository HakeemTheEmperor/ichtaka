from fastapi import APIRouter
from sqlalchemy.orm import Session
from src.auth.auth_dependencies import DB_SESSION, CURRENT_USER
from src.auth.models import User_Account
from . import service, schemas
from src.core.schemas import APIResponse
from src.core.utils.response import SuccessResponse
from src.post.schemas import PostResponse
from typing import List

router = APIRouter()

@router.get("", response_model=APIResponse[schemas.SearchResults])
async def search(
    q: str,
    db: DB_SESSION,
    user: CURRENT_USER
):
    results = service.search_all(db, q, user)
    return SuccessResponse(message="Search results fetched", data=results)

@router.get("/trending", response_model=APIResponse[List[PostResponse]])
async def get_trending(
    db: DB_SESSION
):
    trending = service.get_trending_posts(db)
    return SuccessResponse(message="Trending posts fetched", data=trending)

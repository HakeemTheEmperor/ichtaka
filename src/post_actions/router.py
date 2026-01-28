from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from . import service, schemas
from src.post.router import get_valid_post_id
from src.auth.auth_dependencies import DB_SESSION, get_current_user, CURRENT_USER
from src.core.schemas import APIResponse

router = APIRouter()

@router.post("/{id}/comments", response_model=APIResponse[schemas.CommentResponse], status_code=status.HTTP_201_CREATED)
async def add_comment(
    id: str,
    data: schemas.CommentCreate,
    db: DB_SESSION,
    user: CURRENT_USER
):
    post_id = get_valid_post_id(id)
    comment = await service.add_comment(db, user, post_id, data)
    resp = schemas.CommentResponse.from_attributes(comment)
    resp.pseudonym = user.pseudonym
    return {"message": "Comment added successfully", "code": 201, "data": resp}

@router.post("/{id}/vote", response_model=APIResponse[Any]) # Use Any or refine schema if needed
async def cast_vote(
    id: str,
    vote_data: schemas.VoteRequest,
    db: DB_SESSION,
    user: CURRENT_USER
):
    post_id = get_valid_post_id(id)
    post = await service.cast_vote(db, user, post_id, vote_data.vote_type)
    # Return message and maybe truncated post data or just success
    return {"message": "Vote recorded", "code": 200, "data": None}

@router.patch("/{id}/status", response_model=APIResponse[Any])
async def update_status(
    id: str,
    data: schemas.StatusUpdate,
    db: DB_SESSION
):
    # TODO: Add admin check
    post_id = get_valid_post_id(id)
    post = await service.update_post_status(db, post_id, data.status)
    return {"message": f"Status updated to {data.status}", "code": 200, "data": None}

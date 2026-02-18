from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from . import service, schemas
from src.post.router import get_valid_post_id
from src.auth.auth_dependencies import DB_SESSION, get_current_user, CURRENT_USER
from src.core.schemas import APIResponse
from src.core.utils.response import SuccessResponse

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
    resp = schemas.CommentResponse.model_validate(comment)
    resp.pseudonym = user.pseudonym
    return SuccessResponse(
        message="Comment added successfully", 
        code=status.HTTP_201_CREATED, 
        data=resp
    )

@router.get("/{id}/comments", response_model=APIResponse[list[schemas.CommentResponse]])
async def get_comments(
    id: str,
    db: DB_SESSION
):
    post_id = get_valid_post_id(id)
    comments = service.get_comments(db, post_id)
    return SuccessResponse(
        message="Comments fetched successfully", 
        code=status.HTTP_200_OK, 
        data=comments
    )

@router.post("/{id}/vote", response_model=APIResponse[Any]) # Use Any or refine schema if needed
async def cast_vote(
    id: str,
    vote_data: schemas.VoteRequest,
    db: DB_SESSION,
    user: CURRENT_USER
):
    post_id = get_valid_post_id(id)
    return await service.cast_vote(db, user, post_id, vote_data.vote_type)
    


@router.patch("/{id}/status", response_model=APIResponse[Any])
async def update_status(
    id: str,
    data: schemas.StatusUpdate,
    db: DB_SESSION
):
    # TODO: Add admin check
    post_id = get_valid_post_id(id)
    post = await service.update_post_status(db, post_id, data.status)
    return SuccessResponse(
        message=f"Status updated to {data.status}", 
        code=status.HTTP_200_OK, 
        data=None
    )

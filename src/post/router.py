from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from . import service, schemas, models
from src.auth.auth_dependencies import DB_SESSION, get_current_user, CURRENT_USER, get_optional_current_user
from src.auth.models.user_account import User_Account
from src.core.schemas import APIResponse
from src.utils.encoding import decode_ids

router = APIRouter()

def get_valid_post_id(id: str) -> int:
    try:
        return decode_ids(id)
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid post ID format")

def enrich_comment(comment_obj, comment_schema):
    if comment_obj.author:
        comment_schema.pseudonym = comment_obj.author.pseudonym
    for sub_obj, sub_schema in zip(comment_obj.replies, comment_schema.replies):
        enrich_comment(sub_obj, sub_schema)

@router.post("/", response_model=APIResponse[schemas.PostResponse], status_code=status.HTTP_201_CREATED)
async def create_post(
    data: schemas.PostCreate,
    db: DB_SESSION,
    user: CURRENT_USER
):
    return await service.create_post(db, user, data)
    

@router.get("/", response_model=APIResponse[schemas.FeedResponse])
async def get_feed(
    db: DB_SESSION,
    user: Optional[User_Account] = Depends(get_optional_current_user), # Use dependency directly or define alias in router
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    pseudonym: Optional[str] = Query(None)
):
    return service.get_feed(db, page, limit, user, pseudonym)

@router.get("/{id}", response_model=APIResponse[schemas.PostResponse])
async def get_post(
    id: str,
    db: DB_SESSION,
    user: Optional[User_Account] = Depends(get_optional_current_user)
):
    post_id = get_valid_post_id(id)
    post = service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    resp = schemas.PostResponse.from_attributes(post)
    if post.author:
            resp.pseudonym = post.author.pseudonym
    
    # Check for user vote
    if user:
        from src.post_actions.models import Vote
        vote = db.query(Vote).filter(Vote.post_id == post.id, Vote.user_id == user.id).first()
        if vote:
            resp.user_vote_status = vote.vote_type.value
            
    root_comments_objs = [c for c in post.comments if c.parent_id is None]
    from src.post_actions.schemas import CommentResponse
    resp.comments = [CommentResponse.model_validate(c) for c in root_comments_objs]
    
    for c_obj, c_schema in zip(root_comments_objs, resp.comments):
        enrich_comment(c_obj, c_schema)
        
    return {"message": "Post fetched successfully", "code": 200, "data": resp}

@router.put("/{id}", response_model=APIResponse[schemas.PostResponse])
async def update_post(
    id: str,
    data: schemas.PostUpdate,
    db: DB_SESSION,
    user: CURRENT_USER
):
    post_id = get_valid_post_id(id)
    # Optional: Add ownership check here
    post = await service.update_post(db, post_id, data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    resp = schemas.PostResponse.from_attributes(post)
    if post.author:
        resp.pseudonym = post.author.pseudonym
    return {"message": "Post updated successfully", "code": 200, "data": resp}

@router.delete("/{id}")
async def delete_post(
    id: str,
    db: DB_SESSION,
    user: CURRENT_USER
):
    post_id = get_valid_post_id(id)
    # Optional: Add ownership check here
    if not await service.delete_post(db, post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully", "code": 200, "data": None}

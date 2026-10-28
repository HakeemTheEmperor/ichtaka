from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, noload, selectinload
from fastapi import status
from .models import Post, PostStatus
from .schemas import PostCreate, PostUpdate, PostResponse, FeedResponse
from src.auth.models.user_account import User_Account
from src.core.websocket_manager import manager
from src.core.utils.response import SuccessResponse
from src.notifications.service import create_notification
from src.utils.encoding import encode_ids
import asyncio
import math
import time

async def create_post(db: Session, user: User_Account, data: PostCreate) -> SuccessResponse :
    new_post = Post(
        user_id=user.id if user else None,
        title=data.title,
        description=data.description,
        file_url=data.file_url,
        file_type=data.file_type,
        location=data.location,
        source_url=data.source_url,
        severity=data.severity
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Broadcast new post
    await manager.broadcast({
        "event": "new_post",
        "data": {
            "id": new_post.id,
            "title": new_post.title,
            "severity": new_post.severity if new_post.severity else None,
            "created_at": new_post.created_at.isoformat() if new_post.created_at else None
        }
    })
    
    # Notify followers
    if user:
        for f in user.followers:
            asyncio.create_task(create_notification(
                recipient_id=f.follower_id,
                type="new_post",
                message=f"{user.pseudonym} just posted: {new_post.title[:30]}...",
                sender_id=user.id,
                post_id=encode_ids(new_post.id)
            ))
    
    resp = PostResponse.model_validate(new_post)
    resp.pseudonym = user.pseudonym
    
    # Send post to AI agent for moderation
    # from src.config import settings
    # import httpx
    
    # encoded_id = encode_ids(new_post.id)
    # payload = {
    #     "report_id": encoded_id,
    #     "text": new_post.description,
    #     "image_url": new_post.file_url if new_post.file_url else None
    # }
    
    # headers = {
    #     "Authorization": f"Bearer {settings.AGENT_API_KEY}"
    # }
    
    # try:
    #     async with httpx.AsyncClient() as client:
    #         await client.post(f"{settings.AGENT_URL}/v1/analyze", json=payload, headers=headers)
    # except Exception as e:
    #     print(f"Failed to send post to AI agent: {e}")
    
    return SuccessResponse(
        message="Post created successfully", 
        code=status.HTTP_201_CREATED, 
        data=resp
    )
    


def enrich_comment(comment_obj, comment_schema):
    if comment_obj.author:
        comment_schema.pseudonym = comment_obj.author.pseudonym
    for sub_obj, sub_schema in zip(comment_obj.replies, comment_schema.replies):
        enrich_comment(sub_obj, sub_schema)

# COUNT(*) over the whole posts table runs on every feed request and gets slower as the
# table grows. The page count only needs to be roughly right, so reuse it for a few seconds.
_TOTAL_TTL_SECONDS = 5
_total_cache = {"value": 0, "expires": 0.0}

def _cached_total_posts(query) -> int:
    now = time.monotonic()
    if now >= _total_cache["expires"]:
        _total_cache["value"] = query.count()
        _total_cache["expires"] = now + _TOTAL_TTL_SECONDS
    return _total_cache["value"]

def get_comment_counts(db: Session, post_ids: list[int]) -> dict[int, int]:
    from src.post_actions.models import Comment
    if not post_ids:
        return {}
    rows = (
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
        .all()
    )
    return {post_id: n for post_id, n in rows}

def get_feed(db: Session, page: int = 1, limit: int = 10, user: User_Account = None, pseudonym: str = None):
    query = db.query(Post).options(joinedload(Post.author), noload(Post.comments))
    
    if pseudonym:
        query = query.join(User_Account).filter(User_Account.pseudonym == pseudonym)
    
    # For admins copy this line
    # if status_filter:
    #     query = query.filter(Post.status == status_filter)
    
    # query = query.filter(Post.status == PostStatus.CONFIRMED)
    
    total = query.count() if pseudonym else _cached_total_posts(query)
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Batch fetch votes if user is logged in
    user_votes_map = {}
    if user:
        from src.post_actions.models import Vote
        post_ids = [p.id for p in posts]
        votes = db.query(Vote).filter(
            Vote.post_id.in_(post_ids),
            Vote.user_id == user.id
        ).all()
        user_votes_map = {v.post_id: v.vote_type.value for v in votes}
    
    comment_counts = get_comment_counts(db, [p.id for p in posts])

    post_responses = []
    for p in posts:
        resp = PostResponse.model_validate(p)
        if p.author:
            resp.pseudonym = p.author.pseudonym
        
        # Set user vote status
        resp.user_vote_status = user_votes_map.get(p.id, "none")
            
        resp.comments_count = comment_counts.get(p.id, 0)
        resp.comments = []
        
        # for c_obj, c_schema in zip(root_comments_objs, resp.comments):
        #    enrich_comment(c_obj, c_schema)
            
        post_responses.append(resp)
    data = FeedResponse(posts=post_responses, total=total, page=page, limit=limit, totalPages=math.ceil(total/limit))
    return SuccessResponse(
        message="Posts fetched successfully", 
        code=status.HTTP_200_OK, 
        data=data
    )
        

def get_post(db: Session, post_id: int) -> Post:
    from src.post_actions.models import Comment
    return (
        db.query(Post)
        .options(
            joinedload(Post.author),
            selectinload(Post.comments).joinedload(Comment.author),
            selectinload(Post.comments).selectinload(Comment.replies).joinedload(Comment.author),
        )
        .filter(Post.id == post_id)
        .first()
    )

async def update_post(db: Session, post_id: int, data: PostUpdate) -> Post:
    post = get_post(db, post_id)
    if not post:
        return None

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    
    # Broadcast update
    await manager.broadcast({
        "event": "update_post",
        "data": {
            "id": post.id,
            "status": post.status.value if post.status else None
        }
    })
    
    return post

async def delete_post(db: Session, post_id: int) -> bool:
    post = get_post(db, post_id)
    if not post:
        return False

    db.delete(post)
    db.commit()
    
    # Broadcast deletion
    await manager.broadcast({
        "event": "delete_post",
        "data": {"id": post_id}
    })
    
    return True

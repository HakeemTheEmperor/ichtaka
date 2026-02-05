from sqlalchemy.orm import Session
from fastapi import status
from .models import Post, PostStatus
from .schemas import PostCreate, PostUpdate, PostResponse, FeedResponse
from src.auth.models.user_account import User_Account
from src.core.websocket_manager import manager
from src.core.utils.response import SuccessResponse
import math

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
    
    resp = PostResponse.model_validate(new_post)
    resp.pseudonym = user.pseudonym
    
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

def get_feed(db: Session, page: int = 1, limit: int = 10, user: User_Account = None):
    query = db.query(Post)
    
    # For admins copy this line
    # if status_filter:
    #     query = query.filter(Post.status == status_filter)
    
    # query = query.filter(Post.status == PostStatus.CONFIRMED)
    
    total = query.count()
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
    
    post_responses = []
    for p in posts:
        resp = PostResponse.model_validate(p)
        if p.author:
            resp.pseudonym = p.author.pseudonym
        
        # Set user vote status
        resp.user_vote_status = user_votes_map.get(p.id, "none")
            
        # Lazy loading comments: just count them
        resp.comments_count = len(p.comments) # This uses the relationship, might trigger load if not careful, but usually acceptable for small sets or joined query. 
        # Ideally using a count query is better for performance but this is a start.
        # Actually p.comments might be lazy loaded. 
        # Let's clean comments list to avoid huge payload
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
    return db.query(Post).filter(Post.id == post_id).first()

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

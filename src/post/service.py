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
    

def get_feed(db: Session, page: int = 1, limit: int = 10):
    query = db.query(Post)
    
    # For admins copy this line
    # if status_filter:
    #     query = query.filter(Post.status == status_filter)
    
    # query = query.filter(Post.status == PostStatus.CONFIRMED)
    
    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    post_responses = []
    for p in posts:
        resp = PostResponse.model_validate(p)
        if p.author:
            resp.pseudonym = p.author.pseudonym
            
        # Map only root comments
        root_comments_objs = [c for c in p.comments if c.parent_id is None]
        from src.post_actions.schemas import CommentResponse # Import here to avoid circularity if any
        resp.comments = [CommentResponse.from_attributes(c) for c in root_comments_objs]
        
        for c_obj, c_schema in zip(root_comments_objs, resp.comments):
            enrich_comment(c_obj, c_schema)
            
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

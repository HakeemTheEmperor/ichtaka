from sqlalchemy.orm import Session
from .models import Post, PostStatus
from .schemas import PostCreate, PostUpdate
from src.auth.models.user_account import User_Account
from src.core.websocket_manager import manager

async def create_post(db: Session, user: User_Account, data: PostCreate) -> Post:
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
            "severity": new_post.severity.value if new_post.severity else None,
            "created_at": new_post.created_at.isoformat() if new_post.created_at else None
        }
    })
    
    return new_post

def get_feed(db: Session, page: int = 1, limit: int = 10, status_filter: PostStatus = None):
    query = db.query(Post)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    
    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return posts, total

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

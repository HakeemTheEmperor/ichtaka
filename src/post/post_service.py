from sqlalchemy.orm import Session
from src.models.post import Post
from src.schemas.post import PostCreate, PostUpdate

def create_post(db: Session, data: PostCreate) -> Post:
    post = Post(**data.dict())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def get_feed(db: Session):
    return db.query(Post).order_by(Post.created_at.desc()).all()

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def update_post(db: Session, post_id: int, data: PostUpdate):
    post = get_post(db, post_id)
    if not post:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post

def delete_post(db: Session, post_id: int):
    post = get_post(db, post_id)
    if not post:
        return None

    db.delete(post)
    db.commit()
    return post

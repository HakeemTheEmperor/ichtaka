from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.post.models import Post, PostStatus
from .models import Comment, Vote, VoteType
from .schemas import CommentCreate, VoteRequest
from src.auth.models.user_account import User_Account
from src.utils.encoding import decode_base62
from src.core.websocket_manager import manager

async def add_comment(db: Session, user: User_Account, post_id: int, data: CommentCreate):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    parent_id = None
    if data.parent_id:
        try:
            parent_id = decode_base62(data.parent_id)
        except (ValueError, KeyError):
            raise HTTPException(status_code=400, detail="Invalid parent_id format")
            
        parent = db.query(Comment).filter(Comment.id == parent_id, Comment.post_id == post_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        
        # Enforce 2-layer depth limit
        if parent.parent_id is not None:
            grandfather = db.query(Comment).filter(Comment.id == parent.parent_id).first()
            if grandfather and grandfather.parent_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Maximum comment depth reached (only 2 layers of nesting allowed)"
                )

    new_comment = Comment(
        post_id=post_id,
        user_id=user.id,
        content=data.content,
        parent_id=parent_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # Broadcast new comment
    await manager.broadcast({
        "event": "new_comment",
        "data": {
            "post_id": post_id,
            "comment_id": new_comment.id,
            "parent_id": data.parent_id,
            "created_at": new_comment.created_at.isoformat() if new_comment.created_at else None
        }
    })
    
    return new_comment

async def cast_vote(db: Session, user: User_Account, post_id: int, vote_type: VoteType):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    existing_vote = db.query(Vote).filter(
        Vote.post_id == post_id,
        Vote.user_id == user.id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Toggle off
            db.delete(existing_vote)
            if vote_type == VoteType.UPVOTE:
                post.upvotes_count -= 1
            else:
                post.downvotes_count -= 1
        else:
            # Change vote type
            old_type = existing_vote.vote_type
            existing_vote.vote_type = vote_type
            if vote_type == VoteType.UPVOTE:
                post.upvotes_count += 1
                post.downvotes_count -= 1
            else:
                post.downvotes_count += 1
                post.upvotes_count -= 1
    else:
        # New vote
        new_vote = Vote(
            post_id=post_id,
            user_id=user.id,
            vote_type=vote_type
        )
        db.add(new_vote)
        if vote_type == VoteType.UPVOTE:
            post.upvotes_count += 1
        else:
            post.downvotes_count += 1
            
    db.commit()
    db.refresh(post)
    
    # Broadcast vote update
    await manager.broadcast({
        "event": "vote_update",
        "data": {
            "post_id": post_id,
            "upvotes": post.upvotes_count,
            "downvotes": post.downvotes_count
        }
    })
    
    return post

async def update_post_status(db: Session, post_id: int, new_status: PostStatus):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = new_status
    db.commit()
    db.refresh(post)
    
    # Broadcast status update
    await manager.broadcast({
        "event": "status_update",
        "data": {
            "post_id": post_id,
            "status": new_status.value
        }
    })
    
    return post

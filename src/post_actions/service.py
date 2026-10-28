from sqlalchemy.orm import Session, noload
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException, status
from src.post.models import Post, PostStatus
from .models import Comment, Vote, VoteType
from .schemas import CommentCreate, VoteRequest
from src.auth.models.user_account import User_Account
from src.core.utils.response import SuccessResponse
from src.notifications.service import create_notification
from src.core.websocket_manager import manager
from src.utils.encoding import decode_ids, encode_ids
import asyncio

def _insert_comment(db: Session, user: User_Account, post_id: int, data: CommentCreate):
    post = db.query(Post).options(noload(Post.comments)).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    parent_id = None
    if data.parent_id:
        try:
            parent_id = decode_ids(data.parent_id)
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
    return new_comment, post.user_id, post.title

async def add_comment(db: Session, user: User_Account, post_id: int, data: CommentCreate):
    new_comment, post_author_id, post_title = await run_in_threadpool(_insert_comment, db, user, post_id, data)

    # Broadcast new comment
    await manager.broadcast({
        "event": "new_comment",
        "data": {
            "post_id": post_id,
            "comment_id": new_comment.id,
            "parent_id": data.parent_id,
            "content": new_comment.content,
            "pseudonym": user.pseudonym,
            "created_at": new_comment.created_at.isoformat() if new_comment.created_at else None
        }
    })

    # Notify post author
    if post_author_id and post_author_id != user.id:
        asyncio.create_task(create_notification(
            recipient_id=post_author_id,
            type="comment",
            message=f"{user.pseudonym} commented on your post: {post_title[:30]}...",
            sender_id=user.id,
            post_id=encode_ids(post_id)
        ))

    return new_comment

def _apply_vote(db: Session, user: User_Account, post_id: int, vote_type: VoteType):
    post = db.query(Post).options(noload(Post.comments)).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_vote = db.query(Vote).filter(
        Vote.post_id == post_id,
        Vote.user_id == user.id
    ).first()

    new_vote_status = "none"
    notify = None
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
            existing_vote.vote_type = vote_type
            new_vote_status = vote_type.value
            if vote_type == VoteType.UPVOTE:
                post.upvotes_count += 1
                post.downvotes_count -= 1
            else:
                post.downvotes_count += 1
                post.upvotes_count -= 1
    else:
        # New vote
        db.add(Vote(post_id=post_id, user_id=user.id, vote_type=vote_type))
        new_vote_status = vote_type.value
        if vote_type == VoteType.UPVOTE:
            post.upvotes_count += 1
            # Notify post author on upvote
            if post.user_id and post.user_id != user.id:
                notify = (post.user_id, post.title)
        else:
            post.downvotes_count += 1

    db.commit()
    return new_vote_status, post.upvotes_count, post.downvotes_count, notify

async def cast_vote(db: Session, user: User_Account, post_id: int, vote_type: VoteType):
    new_vote_status, upvotes, downvotes, notify = await run_in_threadpool(_apply_vote, db, user, post_id, vote_type)

    if notify:
        author_id, title = notify
        asyncio.create_task(create_notification(
            recipient_id=author_id,
            type="like",
            message=f"{user.pseudonym} upvoted your post: {title[:30]}...",
            sender_id=user.id,
            post_id=encode_ids(post_id)
        ))

    # Broadcast vote update
    await manager.broadcast({
        "event": "vote_update",
        "data": {
            "post_id": post_id,
            "upvotes": upvotes,
            "downvotes": downvotes
        }
    })

    return SuccessResponse(
        message="Vote recorded",
        code=status.HTTP_200_OK,
        data={
            "user_vote_status": new_vote_status,
            "upvotes": upvotes,
            "downvotes": downvotes
        }
    )

async def update_post_status(db: Session, post_id: int, new_status: PostStatus):
    post = db.query(Post).options(noload(Post.comments)).filter(Post.id == post_id).first()
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

def enrich_comment(comment_obj, comment_schema):
    if comment_obj.author:
        comment_schema.pseudonym = comment_obj.author.pseudonym
    for sub_obj, sub_schema in zip(comment_obj.replies, comment_schema.replies):
        enrich_comment(sub_obj, sub_schema)

def get_comments(db: Session, post_id: int):
    # Fetch all top-level comments for the post
    # Eager loading replies would be good but standard lazy loading might suffice for now
    # We filter by parent_id IS NULL to get roots
    root_comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()
    
    from .schemas import CommentResponse
    comment_responses = [CommentResponse.model_validate(c) for c in root_comments]
    
    for c_obj, c_schema in zip(root_comments, comment_responses):
        enrich_comment(c_obj, c_schema)
        
    return comment_responses

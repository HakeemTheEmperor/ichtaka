from sqlalchemy.orm import Session, joinedload, noload, selectinload
from sqlalchemy import or_, desc, func
import time
from datetime import datetime, timedelta
from src.post.models import Post
from src.auth.models import User_Account, Follow
from src.post_actions.models import Comment, Vote
from src.post.schemas import PostResponse
from src.auth.auth_schemas import UserListResponse
from src.search.schemas import SearchResults
from src.post.service import get_comment_counts

def search_all(db: Session, query_str: str, current_user: User_Account = None) -> SearchResults:
    # Search Posts
    posts = db.query(Post).options(joinedload(Post.author), noload(Post.comments)).filter(
        or_(
            Post.title.ilike(f"%{query_str}%"),
            Post.description.ilike(f"%{query_str}%")
        )
    ).limit(20).all()
    
    counts = get_comment_counts(db, [p.id for p in posts])
    post_responses = []
    for p in posts:
        resp = PostResponse.model_validate(p)
        resp.pseudonym = p.author.pseudonym if p.author else "Anonymous"
        resp.comments_count = counts.get(p.id, 0)
        resp.comments = []
        post_responses.append(resp)
        
    # Search Users
    users = db.query(User_Account).filter(
        User_Account.pseudonym.ilike(f"%{query_str}%")
    ).limit(20).all()
    
    user_responses = []
    for u in users:
        is_following = False
        if current_user:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user.id,
                Follow.followed_id == u.id
            ).first() is not None
        user_responses.append(UserListResponse(pseudonym=u.pseudonym, is_following=is_following))
        
    return SearchResults(posts=post_responses, users=user_responses)

# Trending is the same for every visitor and only needs to be roughly current, but it
# aggregates a week of posts and comments, so reuse the result for a short time.
_TRENDING_TTL_SECONDS = 30
_trending_cache = {"limit": None, "value": [], "expires": 0.0}

def get_trending_posts(db: Session, limit: int = 5):
    now = time.monotonic()
    if _trending_cache["limit"] == limit and now < _trending_cache["expires"]:
        return _trending_cache["value"]
    result = _compute_trending_posts(db, limit)
    _trending_cache.update(limit=limit, value=result, expires=now + _TRENDING_TTL_SECONDS)
    return result

def _compute_trending_posts(db: Session, limit: int):
    # Trending = (upvotes + comments) in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # This is a simplified trending algorithm
    trending_posts = db.query(
        Post,
        (Post.upvotes_count + func.count(Comment.id)).label("score")
    ).outerjoin(Comment).options(selectinload(Post.author), noload(Post.comments)).filter(
        Post.created_at >= seven_days_ago
    ).group_by(Post.id).order_by(desc("score")).limit(limit).all()
    
    # trending_posts is a list of tuples (Post, score)
    counts = get_comment_counts(db, [p.id for p, _ in trending_posts])
    result = []
    for p, score in trending_posts:
        resp = PostResponse.model_validate(p)
        resp.pseudonym = p.author.pseudonym if p.author else "Anonymous"
        resp.comments_count = counts.get(p.id, 0)
        resp.comments = []
        result.append(resp)
        
    return result

from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from datetime import datetime, timedelta
from src.post.models import Post
from src.auth.models import User_Account, Follow
from src.post_actions.models import Comment, Vote
from src.post.schemas import PostResponse
from src.auth.auth_schemas import UserListResponse
from src.search.schemas import SearchResults

def search_all(db: Session, query_str: str, current_user: User_Account = None) -> SearchResults:
    # Search Posts
    posts = db.query(Post).filter(
        or_(
            Post.title.ilike(f"%{query_str}%"),
            Post.description.ilike(f"%{query_str}%")
        )
    ).limit(20).all()
    
    post_responses = []
    for p in posts:
        resp = PostResponse.model_validate(p)
        resp.pseudonym = p.author.pseudonym if p.author else "Anonymous"
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

def get_trending_posts(db: Session, limit: int = 5):
    # Trending = (upvotes + comments) in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # This is a simplified trending algorithm
    trending_posts = db.query(
        Post,
        (Post.upvotes_count + func.count(Comment.id)).label("score")
    ).outerjoin(Comment).filter(
        Post.created_at >= seven_days_ago
    ).group_by(Post.id).order_by(desc("score")).limit(limit).all()
    
    # trending_posts is a list of tuples (Post, score)
    result = []
    for p, score in trending_posts:
        resp = PostResponse.model_validate(p)
        resp.pseudonym = p.author.pseudonym if p.author else "Anonymous"
        result.append(resp)
        
    return result

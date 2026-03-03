from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.agent.schemas import AnalyzeCallback
from src.auth.auth_dependencies import DB_SESSION
from src.post.models import Post, PostStatus
from src.config import settings

router = APIRouter()
security = HTTPBearer()

def verify_agent_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Agent API Key")
    return credentials.credentials

@router.post("/callback", status_code=200)
async def agent_callback(
    payload: AnalyzeCallback,
    db: DB_SESSION,
    api_key: str = Depends(verify_agent_api_key)
):
    from src.post.router import get_valid_post_id
    from src.core.websocket_manager import manager
    
    post_id = get_valid_post_id(payload.report_id)
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # Update post status based on verdict
    if payload.verdict == "auto-approve":
        post.status = PostStatus.CONFIRMED
    elif payload.verdict == "auto-reject":
        post.status = PostStatus.REFUTED
    elif payload.verdict == "escalate":
        post.status = PostStatus.UNVERIFIED  # Requires manual review
        
    # We could also save payload.flags, payload.pii_found, and payload.integral_score
    # into a dedicated Moderation log table or extra columns if they exist.
    
    db.commit()
    db.refresh(post)
    
    # Broadcast the status update to connected clients
    await manager.broadcast({
        "event": "update_post",
        "data": {
            "id": post.id,
            "status": post.status.value
        }
    })
    
    return {"status": "success", "message": "Callback received and processed"}

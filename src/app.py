from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .core.websocket_manager import manager
from .auth import auth_router 
from .post.router import router as posts_router
from .post_actions.router import router as post_actions_router
from .notifications.router import router as notifications_router
from .search.router import router as search_router
from src.core.errors.exception_handlers import (app_exception_handler, unhandled_exception_handler)
from src.core.errors.base_exception import AppException
from src.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

# Import all models here so Base.metadata knows about them
from src.auth.models.user_account import User_Account
from src.post.models import Post
from src.post_actions.models import Comment, Vote
from src.notifications.models import Notification

app = FastAPI(title="Ichtaka API", description="Secure, anonymous reporting and social platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(
    auth_router.router,
    prefix="/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    posts_router,
    prefix="/v1/posts",
    tags=["Posts"]
)

app.include_router(
    post_actions_router,
    prefix="/v1/posts/actions",
    tags=["Post Actions"]
)

app.include_router(
    notifications_router,
    prefix="/v1/notifications",
    tags=["Notifications"]
)

app.include_router(
    search_router,
    prefix="/v1/search",
    tags=["Search"]
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to Ichtaka API"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    # For simplicity, we can pass token as query param
    if not token:
        await websocket.close(code=1008)
        return
    
    import jwt
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Respond to ping or other control messages if necessary
            await manager.send_personal_message({"type": "pong", "data": data}, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

def start():
    """Launched with `uv run start` at root level"""
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
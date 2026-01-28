from fastapi import FastAPI
from .auth import auth_router 
from .post.router import router as posts_router
from .post_actions.router import router as post_actions_router
from src.core.errors.exception_handlers import (app_exception_handler, unhandled_exception_handler)
from src.core.errors.base_exception import AppException
from src.database import Base, engine

# Import all models here so Base.metadata knows about them
from src.auth.models.user_account import User_Account
from src.post.models import Post
from src.post_actions.models import Comment, Vote

app = FastAPI(title="Ichtaka API", description="Secure, anonymous reporting and social platform")

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

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to Ichtaka API"}

def start():
    """Launched with `uv run start` at root level"""
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
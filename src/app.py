from fastapi import FastAPI
from .auth import auth_router 
from .post import post_router
from src.core.errors.exception_handlers import (app_exception_handler, unhandled_exception_handler)
from src.core.errors.base_exception import AppException
from src.database import Base, engine

app = FastAPI(title="Ichtaka Reports API", description="Secure, anonymous reporting platform")

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(
    auth_router.router,
    prefix="/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    post_router.router,
    prefix="/v1/post",
    tags=["Posts"]
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to Ichtaka API"}
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import settings

SQL_ALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(
    SQL_ALCHEMY_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False, bind=engine)

Base = declarative_base()

# async so that creating and closing the session runs on the event loop instead of
# needing a threadpool slot. A connection is only checked out lazily on first query;
# if closing it required a worker thread while every worker was blocked waiting for a
# pooled connection, the pool would deadlock under load.
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from sqlalchemy import Index, Column, String, BigInteger, JSON, ForeignKey, Enum, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
from datetime import datetime
import enum

class PostStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    # Additional statuses for general posts if needed can be added here
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    file_url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # image | video | file
    
    location = Column(JSON, nullable=True)
    source_url = Column(String, nullable=True)
    
    severity = Column(String(20), nullable=False, default="medium")
    status = Column(Enum(PostStatus), default=PostStatus.UNVERIFIED, nullable=False)
    
    upvotes_count = Column(Integer, default=0, nullable=False)
    downvotes_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_posts_created_at", "created_at"),
        Index("ix_posts_user_id", "user_id"),
        Index("ix_posts_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
        Index("ix_posts_description_trgm", "description", postgresql_using="gin", postgresql_ops={"description": "gin_trgm_ops"}),
    )

    # Relationships
    author = relationship("User_Account", backref="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="post", cascade="all, delete-orphan")

from sqlalchemy import Column, BigInteger, ForeignKey, Enum, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime
import enum

class VoteType(str, enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

class Comment(Base):
    __tablename__ = "post_comments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=False)
    parent_id = Column(BigInteger, ForeignKey("post_comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User_Account", backref="post_comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

class Vote(Base):
    __tablename__ = "post_votes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=False)
    vote_type = Column(Enum(VoteType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='_post_user_vote_uc'),)
    
    # Relationships
    post = relationship("Post", back_populates="votes")
    user = relationship("User_Account", backref="post_votes")

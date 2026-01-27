from sqlalchemy import Column, String, BigInteger, JSON, ForeignKey, Enum, DateTime, Text, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime
import enum

class ReportStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"

class VoteType(str, enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    location = Column(JSON, nullable=True)
    source_url = Column(String, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.UNVERIFIED, nullable=False)
    
    upvotes_count = Column(Integer, default=0, nullable=False)
    downvotes_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User_Account", backref="reports")
    comments = relationship("Comment", back_populates="report", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="report", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("Report", back_populates="comments")
    author = relationship("User_Account", backref="comments")

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=False)
    vote_type = Column(Enum(VoteType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('report_id', 'user_id', name='_report_user_vote_uc'),)
    
    # Relationships
    report = relationship("Report", back_populates="votes")
    user = relationship("User_Account", backref="votes")

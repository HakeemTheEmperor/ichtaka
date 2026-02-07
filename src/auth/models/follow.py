from sqlalchemy import Column, Integer, BigInteger, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(BigInteger, ForeignKey("user_account.id"), primary_key=True)
    followed_id = Column(BigInteger, ForeignKey("user_account.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    follower = relationship("User_Account", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User_Account", foreign_keys=[followed_id], back_populates="followers")

    __table_args__ = (
        UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),
    )

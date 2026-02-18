from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from src.database import Base

class NotificationType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    NEW_POST = "new_post"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True)
    recipient_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=False)
    sender_id = Column(BigInteger, ForeignKey("user_account.id"), nullable=True)
    type = Column(String, nullable=False) # Store NotificationType value
    post_id = Column(String, nullable=True) # ID of the post involved
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipient = relationship("User_Account", foreign_keys=[recipient_id], backref="notifications")
    sender = relationship("User_Account", foreign_keys=[sender_id])

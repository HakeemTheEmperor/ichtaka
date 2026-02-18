from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    recipient_id: int
    sender_id: Optional[int]
    type: str # NotificationType
    post_id: Optional[str]
    message: str
    is_read: bool = False

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime
    sender_pseudonym: Optional[str] = None

    class Config:
        from_attributes = True

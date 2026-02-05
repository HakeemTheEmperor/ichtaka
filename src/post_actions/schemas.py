from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Any
from datetime import datetime
from src.utils.encoding import encode_ids
from src.post.models import PostStatus
from .models import VoteType

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    parent_id: Optional[str] = None # Expecting Base62 string

class CommentResponse(CommentBase):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int] = None
    pseudonym: Optional[str] = None
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True

    @field_serializer("id", "post_id", "parent_id")
    def serialize_ids(self, v: int) -> str:
        if v is None:
            return ""
        return encode_ids(v)

class VoteRequest(BaseModel):
    vote_type: VoteType

class StatusUpdate(BaseModel):
    status: PostStatus

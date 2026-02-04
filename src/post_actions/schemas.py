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
    id: str
    user_id: int
    post_id: str
    parent_id: Optional[str] = None
    pseudonym: Optional[str] = None
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True

    @field_serializer("id", "post_id", "parent_id")
    def encode_ids(self, v: Any) -> Any:
        if v is None:
            return None
        return encode_ids(v)

class VoteRequest(BaseModel):
    vote_type: VoteType

class StatusUpdate(BaseModel):
    status: PostStatus

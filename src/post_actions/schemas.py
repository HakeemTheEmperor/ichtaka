from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from src.utils.encoding import encode_base62
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

    @field_validator("id", "post_id", "parent_id", mode="before")
    @classmethod
    def encode_ids(cls, v: Any, info: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, int):
            return encode_base62(v)
        return str(v)

class VoteRequest(BaseModel):
    vote_type: VoteType

class StatusUpdate(BaseModel):
    status: PostStatus

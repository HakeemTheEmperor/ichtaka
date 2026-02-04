from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Any
from datetime import datetime
from .models import PostStatus
from src.utils.encoding import encode_ids

class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    location: Optional[str] = None
    source_url: Optional[str] = None
    severity: str = "medium"

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    location: Optional[str] = None
    source_url: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[PostStatus] = None

class PostResponse(PostBase):
    id: int
    user_id: Optional[int] = None
    pseudonym: Optional[str] = None
    status: PostStatus
    upvotes_count: int
    downvotes_count: int
    created_at: datetime
    updated_at: datetime
    # Comments will be handled by PostActions schemas or a separate inclusion
    comments: List[Any] = []

    class Config:
        from_attributes = True

    @field_serializer("id")
    def serialize_id(self, v: int) -> str:
        return encode_ids(v)

class FeedResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    limit: int
    totalPages:int

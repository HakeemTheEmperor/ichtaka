from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from .models import ReportStatus, VoteType

# VOTE
class VoteRequest(BaseModel):
    vote_type: VoteType

# COMMENT
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    user_id: int
    pseudonym: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# REPORT
class ReportBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    image_url: Optional[str] = None
    location: Optional[dict] = None
    source_url: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdateStatus(BaseModel):
    status: ReportStatus

class ReportResponse(ReportBase):
    id: int
    user_id: Optional[int]
    pseudonym: Optional[str] = None
    status: ReportStatus
    upvotes_count: int
    downvotes_count: int
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class FeedResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    limit: int

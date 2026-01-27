from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PostBase(BaseModel):
    title: str
    description: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    severity: str
    location: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    location: Optional[str]

class PostResponse(PostBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

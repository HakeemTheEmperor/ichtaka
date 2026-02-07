from pydantic import BaseModel
from typing import List, Optional
from src.post.schemas import PostResponse
from src.auth.auth_schemas import UserListResponse

class SearchResults(BaseModel):
    posts: List[PostResponse]
    users: List[UserListResponse]

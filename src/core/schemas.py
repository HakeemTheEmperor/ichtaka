from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    message: str = 'Success'
    code: int = 200
    error: Optional[str] = None
    data: Optional[T] = None
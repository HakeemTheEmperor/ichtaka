from typing import Generic, TypeVar, Optional
from pydantic.generics import GenericModel

T = TypeVar("DataT")

class APIResponse(GenericModel, Generic[T]):
    message: str = 'Success'
    code: int = 200
    error: Optional[str] = None
    data: Optional[T] = None
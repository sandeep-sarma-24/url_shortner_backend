from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

import math
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel


T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency for paginated endpoints via query parameters."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated list responses."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def paginate(items: list, total: int, params: PaginationParams) -> dict:
    """Convert items + total + params into a PaginatedResponse dict."""
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": math.ceil(total / params.page_size) if total > 0 else 0,
    }

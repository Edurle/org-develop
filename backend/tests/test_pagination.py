"""Unit tests for pagination utilities.

Tests PaginationParams offset calculation and paginate() helper.
These are synchronous tests (no database required).
"""

import math

from app.schemas.common import PaginationParams, PaginatedResponse, paginate


class TestPagination:

    def test_pagination_defaults(self):
        p = PaginationParams(page=1, page_size=20)
        assert p.offset == 0
        assert p.page == 1
        assert p.page_size == 20

    def test_pagination_page2(self):
        p = PaginationParams(page=2, page_size=10)
        assert p.offset == 10
        assert p.page == 2
        assert p.page_size == 10

    def test_pagination_page3(self):
        p = PaginationParams(page=3, page_size=15)
        assert p.offset == 30

    def test_paginate_response(self):
        p = PaginationParams(page=1, page_size=2)
        result = paginate(["a", "b"], 5, p)
        assert result["total"] == 5
        assert result["total_pages"] == 3
        assert result["page"] == 1
        assert result["items"] == ["a", "b"]

    def test_paginate_empty(self):
        p = PaginationParams(page=1, page_size=20)
        result = paginate([], 0, p)
        assert result["total_pages"] == 0
        assert result["items"] == []
        assert result["total"] == 0

    def test_paginate_exact_fit(self):
        p = PaginationParams(page=1, page_size=2)
        result = paginate(["a", "b"], 4, p)
        assert result["total_pages"] == 2
        assert result["items"] == ["a", "b"]
        assert result["total"] == 4
        assert result["page"] == 1
        assert result["page_size"] == 2

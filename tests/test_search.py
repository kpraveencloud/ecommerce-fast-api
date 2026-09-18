"""Tests for search tools."""

import pytest
from unittest.mock import patch

from src.ecommerce_mcp.tools.search import (
    search_products,
    get_product_recommendations,
    get_categories,
)
from src.ecommerce_mcp.utils import ValidationError


class TestSearchProducts:
    """Tests for search_products tool."""

    @pytest.mark.asyncio
    async def test_search_products_success(self, patch_httpx):
        """Test product search."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "results": [
                    {
                        "product_id": 1,
                        "name": "Laptop",
                        "price": 999.99,
                        "rating": 4.5,
                    }
                ],
                "total_count": 1,
                "facets": {
                    "categories": ["Electronics"],
                    "price_ranges": {"500-1000": 1},
                    "brands": ["Dell"],
                },
            }

            result = await search_products("laptop")

            assert len(result["results"]) == 1
            assert result["results"][0]["name"] == "Laptop"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_products_with_filters(self, patch_httpx):
        """Test product search with filters."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {"results": [], "total_count": 0}

            await search_products(
                query="laptop",
                categories=["Electronics"],
                price_range={"min": 500, "max": 1500},
                rating_min=4.0,
                brands=["Dell", "HP"],
                sort_by="price_asc",
                limit=10,
            )

            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["q"] == "laptop"
            assert "Electronics" in params["categories"]
            assert params["price_min"] == 500
            assert params["rating_min"] == 4.0

    @pytest.mark.asyncio
    async def test_search_products_invalid_rating(self, patch_httpx):
        """Test search with invalid rating."""
        with pytest.raises(ValidationError):
            await search_products(
                query="laptop",
                rating_min=6.0,  # Max is 5.0
            )

    @pytest.mark.asyncio
    async def test_search_products_invalid_price_range(self, patch_httpx):
        """Test search with invalid price range."""
        with pytest.raises(ValidationError):
            await search_products(
                query="laptop",
                price_range={"min": 1500, "max": 500},  # min > max
            )

    @pytest.mark.asyncio
    async def test_search_products_invalid_limit(self, patch_httpx):
        """Test search with invalid limit."""
        with pytest.raises(ValidationError):
            await search_products(
                query="laptop",
                limit=200,  # Max is 100
            )


class TestGetProductRecommendations:
    """Tests for get_product_recommendations tool."""

    @pytest.mark.asyncio
    async def test_get_recommendations_by_product(self, patch_httpx):
        """Test recommendations based on product."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "product_id": 2,
                        "name": "Monitor",
                        "price": 299.99,
                        "match_score": 0.95,
                        "reason": "frequently_bought_together",
                    }
                ]
            }

            result = await get_product_recommendations(
                based_on="product_id",
                id="1",
                recommendation_type="frequently_bought_together",
            )

            assert len(result["data"]) == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recommendations_by_customer(self, patch_httpx):
        """Test recommendations based on customer."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {"data": []}

            await get_product_recommendations(
                based_on="customer_id",
                id="cust_123",
                limit=5,
            )

            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["based_on"] == "customer_id"
            assert params["id"] == "cust_123"
            assert params["limit"] == 5

    @pytest.mark.asyncio
    async def test_recommendations_invalid_based_on(self, patch_httpx):
        """Test with invalid based_on parameter."""
        with pytest.raises(ValidationError):
            await get_product_recommendations(
                based_on="invalid_type",
                id="123",
            )

    @pytest.mark.asyncio
    async def test_recommendations_invalid_type(self, patch_httpx):
        """Test with invalid recommendation type."""
        with pytest.raises(ValidationError):
            await get_product_recommendations(
                based_on="product_id",
                id="1",
                recommendation_type="invalid_type",
            )

    @pytest.mark.asyncio
    async def test_recommendations_invalid_limit(self, patch_httpx):
        """Test with invalid limit."""
        with pytest.raises(ValidationError):
            await get_product_recommendations(
                based_on="product_id",
                id="1",
                limit=100,  # Max is 50
            )


class TestGetCategories:
    """Tests for get_categories tool."""

    @pytest.mark.asyncio
    async def test_get_categories_success(self, patch_httpx):
        """Test retrieving categories."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "category_id": "cat_1",
                        "name": "Electronics",
                        "parent_id": None,
                        "description": "Electronic devices",
                        "product_count": 150,
                        "children": [
                            {
                                "category_id": "cat_2",
                                "name": "Computers",
                                "parent_id": "cat_1",
                            }
                        ],
                    }
                ]
            }

            result = await get_categories(include_product_count=True)

            assert len(result["data"]) == 1
            assert result["data"][0]["product_count"] == 150
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_with_parent(self, patch_httpx):
        """Test retrieving subcategories."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {"data": []}

            await get_categories(parent_category="cat_1")

            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["parent"] == "cat_1"

    @pytest.mark.asyncio
    async def test_get_categories_invalid_parent(self, patch_httpx):
        """Test with invalid parent category."""
        with pytest.raises(ValidationError):
            await get_categories(parent_category="")  # Empty string

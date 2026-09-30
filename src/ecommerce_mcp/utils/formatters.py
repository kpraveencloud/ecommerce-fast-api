"""Response formatting utilities."""

from datetime import UTC, datetime
from typing import Any

from .error_handler import EcommerceMCPError


def format_success_response(data: Any, message: str = "Success") -> dict:
    """Wrap successful response with metadata."""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def format_error_response(error: EcommerceMCPError) -> dict:
    """Wrap error response with metadata."""
    return {
        "status": "error",
        "error_code": error.error_code,
        "message": error.message,
        "details": error.details,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def format_paginated_response(
    items: list[Any],
    limit: int,
    offset: int,
    total: int,
    message: str = "Success",
) -> dict:
    """Wrap paginated response with pagination metadata."""
    return {
        "status": "success",
        "message": message,
        "data": items,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + limit < total,
            "page": offset // limit + 1 if limit > 0 else 1,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


def format_cursor_paginated_response(
    items: list[Any],
    next_cursor: str | None = None,
    has_more: bool = False,
    message: str = "Success",
) -> dict:
    """Wrap cursor-paginated response."""
    return {
        "status": "success",
        "message": message,
        "data": items,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


def format_batch_response(
    updated_count: int,
    failed_count: int,
    errors: list[dict] | None = None,
    message: str = "Batch operation completed",
) -> dict:
    """Wrap batch operation response."""
    return {
        "status": "success",
        "message": message,
        "data": {
            "updated_count": updated_count,
            "failed_count": failed_count,
            "total_count": updated_count + failed_count,
            "success_rate": (
                updated_count / (updated_count + failed_count) * 100
                if (updated_count + failed_count) > 0
                else 0
            ),
        },
        "errors": errors or [],
        "timestamp": datetime.now(UTC).isoformat(),
    }


def format_transaction_response(
    transaction_id: str,
    status: str,
    amount: float,
    currency: str = "USD",
    confirmation_code: str | None = None,
) -> dict:
    """Format transaction response."""
    return format_success_response(
        {
            "transaction_id": transaction_id,
            "status": status,
            "amount": amount,
            "currency": currency,
            "confirmation_code": confirmation_code,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def format_shipment_response(
    shipment_id: str,
    status: str,
    tracking_number: str | None = None,
    carrier: str | None = None,
    estimated_delivery: str | None = None,
) -> dict:
    """Format shipment response."""
    return format_success_response(
        {
            "shipment_id": shipment_id,
            "status": status,
            "tracking_number": tracking_number,
            "carrier": carrier,
            "estimated_delivery": estimated_delivery,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )

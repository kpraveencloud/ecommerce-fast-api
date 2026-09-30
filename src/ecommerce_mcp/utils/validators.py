"""Input validation schemas using Pydantic."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


# Payment Schemas
class PaymentSchema(BaseModel):
    """Validation schema for payment processing."""

    order_id: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_method: Literal["credit_card", "debit_card", "wallet", "bank_transfer"]
    payment_details: dict[str, Any]
    idempotency_key: str | None = None

    class Config:
        json_schema_extra = {  # noqa: RUF012
            "example": {
                "order_id": "ord_123",
                "amount": 99.99,
                "currency": "USD",
                "payment_method": "credit_card",
                "payment_details": {"token": "tok_visa_4242"},
                "idempotency_key": "idem_unique_123",
            }
        }


class RefundSchema(BaseModel):
    """Validation schema for refunds."""

    transaction_id: str
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    reason: Literal[
        "customer_request",
        "defective_item",
        "duplicate_charge",
        "fraud",
        "other",
    ]
    notes: str | None = None


# Shipping Schemas
class AddressSchema(BaseModel):
    """Validation schema for address."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str


class ShipmentItemSchema(BaseModel):
    """Validation schema for shipment items."""

    product_id: str
    quantity: int = Field(gt=0)
    sku: str


class CreateShipmentSchema(BaseModel):
    """Validation schema for shipment creation."""

    order_id: str
    items: list[ShipmentItemSchema]
    carrier: Literal["fedex", "ups", "usps", "dhl"]
    shipping_address: AddressSchema
    shipping_method: Literal["standard", "express", "overnight", "international"]
    signature_required: bool = False


# Inventory Schemas
class StockAdjustmentSchema(BaseModel):
    """Validation schema for inventory adjustment."""

    product_id: int
    warehouse_id: str
    quantity_change: int = Field(ne=0)
    reason: Literal["restock", "damage", "loss", "return", "correction"]
    reference_id: str | None = None
    notes: str | None = None


# Search Schemas
class PriceRangeSchema(BaseModel):
    """Validation schema for price range filter."""

    min: Decimal | None = Field(None, ge=0)
    max: Decimal | None = Field(None, ge=0)

    @validator("max")
    def validate_range(cls, v, values):
        if (
            "min" in values
            and values["min"] is not None
            and v is not None
            and v < values["min"]
        ):
            raise ValueError("max must be >= min")
        return v


class SearchProductsSchema(BaseModel):
    """Validation schema for product search."""

    query: str
    categories: list[str] | None = None
    price_range: PriceRangeSchema | None = None
    rating_min: float | None = Field(None, ge=0, le=5)
    in_stock_only: bool = True
    brands: list[str] | None = None
    sort_by: Literal[
        "relevance", "price_asc", "price_desc", "rating", "newest", "popularity"
    ] = "relevance"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


# Promotions Schemas
class CouponValidationSchema(BaseModel):
    """Validation schema for coupon validation."""

    coupon_code: str
    order_total: Decimal | None = Field(None, gt=0)
    customer_id: str | None = None


class PromotionSchema(BaseModel):
    """Validation schema for promotion creation."""

    name: str
    discount_type: Literal["percentage", "fixed_amount", "buy_x_get_y", "free_shipping"]
    discount_value: Decimal = Field(gt=0)
    start_date: datetime
    end_date: datetime
    applicable_products: list[int] | None = None
    applicable_categories: list[str] | None = None
    max_uses: int | None = Field(None, gt=0)
    customer_tiers: list[str] | None = None
    terms: str | None = None

    @validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


# Communication Schemas
class EmailSchema(BaseModel):
    """Validation schema for email sending."""

    customer_id: str
    email_type: Literal[
        "order_confirmation",
        "shipment_notification",
        "review_request",
        "promotional",
        "support_response",
    ]
    subject: str
    body: str
    template_id: str | None = None
    template_variables: dict[str, Any] | None = None


class ContactPreferencesSchema(BaseModel):
    """Validation schema for contact preferences."""

    customer_id: str
    email_promotional: bool | None = None
    email_updates: bool | None = None
    sms_notifications: bool | None = None
    push_notifications: bool | None = None
    frequency: Literal["daily", "weekly", "monthly"] | None = None


# Returns Schemas
class ReturnItemSchema(BaseModel):
    """Validation schema for return items."""

    product_id: str
    quantity: int = Field(gt=0)
    reason: Literal[
        "defective",
        "wrong_item",
        "not_as_described",
        "changed_mind",
        "damaged_in_shipping",
        "other",
    ]


class CreateReturnSchema(BaseModel):
    """Validation schema for return request creation."""

    order_id: str
    items: list[ReturnItemSchema]
    comments: str | None = None


# Batch Schemas
class ProductImportSchema(BaseModel):
    """Validation schema for product import."""

    name: str
    sku: str
    category: str
    price: Decimal = Field(gt=0, decimal_places=2)
    description: str | None = None
    stock_quantity: int = Field(ge=0)
    supplier_id: str | None = None


class BulkImportProductsSchema(BaseModel):
    """Validation schema for bulk product import."""

    products: list[ProductImportSchema]
    update_existing: bool = False
    file_source: str | None = None


class BulkUpdateOrdersSchema(BaseModel):
    """Validation schema for bulk order updates."""

    order_ids: list[str]
    status: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


# Pagination Schemas
class PaginationParamsSchema(BaseModel):
    """Validation schema for pagination parameters."""

    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# Analytics Schemas
class SalesMetricsSchema(BaseModel):
    """Validation schema for sales metrics request."""

    period: Literal["today", "week", "month", "quarter", "year", "custom"]
    start_date: datetime | None = None
    end_date: datetime | None = None
    breakdown_by: Literal["category", "product", "customer_tier", "region"] | None = (
        None
    )


class ExportReportSchema(BaseModel):
    """Validation schema for report export."""

    report_type: Literal["sales", "inventory", "customers", "orders", "reviews"]
    format: Literal["csv", "pdf", "json"]
    period: Literal["week", "month", "quarter", "year"]
    filters: dict[str, Any] | None = None

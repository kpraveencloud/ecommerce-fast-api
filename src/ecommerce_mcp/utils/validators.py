"""Input validation schemas using Pydantic."""

from typing import List, Optional, Literal, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Payment Schemas
class PaymentSchema(BaseModel):
    """Validation schema for payment processing."""

    order_id: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_method: Literal["credit_card", "debit_card", "wallet", "bank_transfer"]
    payment_details: Dict[str, Any]
    idempotency_key: Optional[str] = None

    class Config:
        json_schema_extra = {
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
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    reason: Literal[
        "customer_request",
        "defective_item",
        "duplicate_charge",
        "fraud",
        "other",
    ]
    notes: Optional[str] = None


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
    items: List[ShipmentItemSchema]
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
    reference_id: Optional[str] = None
    notes: Optional[str] = None


# Search Schemas
class PriceRangeSchema(BaseModel):
    """Validation schema for price range filter."""

    min: Optional[Decimal] = Field(None, ge=0)
    max: Optional[Decimal] = Field(None, ge=0)

    @validator("max")
    def validate_range(cls, v, values):
        if "min" in values and values["min"] is not None and v is not None:
            if v < values["min"]:
                raise ValueError("max must be >= min")
        return v


class SearchProductsSchema(BaseModel):
    """Validation schema for product search."""

    query: str
    categories: Optional[List[str]] = None
    price_range: Optional[PriceRangeSchema] = None
    rating_min: Optional[float] = Field(None, ge=0, le=5)
    in_stock_only: bool = True
    brands: Optional[List[str]] = None
    sort_by: Literal["relevance", "price_asc", "price_desc", "rating", "newest", "popularity"] = "relevance"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


# Promotions Schemas
class CouponValidationSchema(BaseModel):
    """Validation schema for coupon validation."""

    coupon_code: str
    order_total: Optional[Decimal] = Field(None, gt=0)
    customer_id: Optional[str] = None


class PromotionSchema(BaseModel):
    """Validation schema for promotion creation."""

    name: str
    discount_type: Literal["percentage", "fixed_amount", "buy_x_get_y", "free_shipping"]
    discount_value: Decimal = Field(gt=0)
    start_date: datetime
    end_date: datetime
    applicable_products: Optional[List[int]] = None
    applicable_categories: Optional[List[str]] = None
    max_uses: Optional[int] = Field(None, gt=0)
    customer_tiers: Optional[List[str]] = None
    terms: Optional[str] = None

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
    template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None


class ContactPreferencesSchema(BaseModel):
    """Validation schema for contact preferences."""

    customer_id: str
    email_promotional: Optional[bool] = None
    email_updates: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    frequency: Optional[Literal["daily", "weekly", "monthly"]] = None


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
    items: List[ReturnItemSchema]
    comments: Optional[str] = None


# Batch Schemas
class ProductImportSchema(BaseModel):
    """Validation schema for product import."""

    name: str
    sku: str
    category: str
    price: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = None
    stock_quantity: int = Field(ge=0)
    supplier_id: Optional[str] = None


class BulkImportProductsSchema(BaseModel):
    """Validation schema for bulk product import."""

    products: List[ProductImportSchema]
    update_existing: bool = False
    file_source: Optional[str] = None


class BulkUpdateOrdersSchema(BaseModel):
    """Validation schema for bulk order updates."""

    order_ids: List[str]
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


# Pagination Schemas
class PaginationParamsSchema(BaseModel):
    """Validation schema for pagination parameters."""

    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# Analytics Schemas
class SalesMetricsSchema(BaseModel):
    """Validation schema for sales metrics request."""

    period: Literal["today", "week", "month", "quarter", "year", "custom"]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    breakdown_by: Optional[Literal["category", "product", "customer_tier", "region"]] = None


class ExportReportSchema(BaseModel):
    """Validation schema for report export."""

    report_type: Literal["sales", "inventory", "customers", "orders", "reviews"]
    format: Literal["csv", "pdf", "json"]
    period: Literal["week", "month", "quarter", "year"]
    filters: Optional[Dict[str, Any]] = None

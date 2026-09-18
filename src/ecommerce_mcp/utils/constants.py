"""Constants and enums for ecommerce MCP."""

from enum import Enum


class PaymentMethod(str, Enum):
    """Payment method types."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    WALLET = "wallet"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(str, Enum):
    """Payment status types."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class RefundReason(str, Enum):
    """Refund reason types."""

    CUSTOMER_REQUEST = "customer_request"
    DEFECTIVE_ITEM = "defective_item"
    DUPLICATE_CHARGE = "duplicate_charge"
    FRAUD = "fraud"
    OTHER = "other"


class ShippingCarrier(str, Enum):
    """Shipping carrier types."""

    FEDEX = "fedex"
    UPS = "ups"
    USPS = "usps"
    DHL = "dhl"


class ShippingMethod(str, Enum):
    """Shipping method types."""

    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    INTERNATIONAL = "international"


class ShipmentStatus(str, Enum):
    """Shipment status types."""

    PENDING = "pending"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    RETURNED = "returned"
    EXCEPTION = "exception"


class InventoryStatus(str, Enum):
    """Inventory status types."""

    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"


class StockAdjustmentReason(str, Enum):
    """Stock adjustment reason types."""

    RESTOCK = "restock"
    DAMAGE = "damage"
    LOSS = "loss"
    RETURN = "return"
    CORRECTION = "correction"


class PromotionType(str, Enum):
    """Promotion discount types."""

    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_X_GET_Y = "buy_x_get_y"
    FREE_SHIPPING = "free_shipping"


class NotificationType(str, Enum):
    """Notification type types."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


class ReturnReason(str, Enum):
    """Return reason types."""

    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    DAMAGED_IN_SHIPPING = "damaged_in_shipping"
    OTHER = "other"


class ReturnStatus(str, Enum):
    """Return status types."""

    REQUESTED = "requested"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    REFUNDED = "refunded"
    REJECTED = "rejected"


class SortOrder(str, Enum):
    """Sort order types."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class ReportType(str, Enum):
    """Report type types."""

    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    ORDERS = "orders"
    REVIEWS = "reviews"


class ExportFormat(str, Enum):
    """Export format types."""

    CSV = "csv"
    PDF = "pdf"
    JSON = "json"


class TimePeriod(str, Enum):
    """Time period types."""

    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class CustomerTier(str, Enum):
    """Customer tier types."""

    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


# API Configuration Constants
DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 1000
MIN_PAGE_LIMIT = 1

DEFAULT_TIMEOUT = 30
PAYMENT_TIMEOUT = 60
SEARCH_TIMEOUT = 15
SHIPPING_TIMEOUT = 20

MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

CACHE_TTL_SECONDS = 300
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

# Error codes
ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_PAYMENT = "PAYMENT_ERROR"
ERROR_PAYMENT_DECLINED = "PAYMENT_DECLINED"
ERROR_INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
ERROR_INVENTORY = "INVENTORY_ERROR"
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_CONFLICT = "CONFLICT"
ERROR_RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
ERROR_TIMEOUT = "TIMEOUT"
ERROR_SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
ERROR_INTERNAL = "INTERNAL_SERVER_ERROR"

# Currency codes
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR"]

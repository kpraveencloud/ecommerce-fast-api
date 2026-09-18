"""Custom exception hierarchy for ecommerce MCP server."""

from typing import Optional, Any


class EcommerceMCPError(Exception):
    """Base exception for all MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code}, message={self.message})"


class ValidationError(EcommerceMCPError):
    """Raised for input validation failures."""

    def __init__(
        self, message: str, details: Optional[dict] = None, error_code: str = "VALIDATION_ERROR"
    ):
        super().__init__(message, error_code, details, 400)


class PaymentError(EcommerceMCPError):
    """Raised for payment processing failures."""

    def __init__(
        self, message: str, details: Optional[dict] = None, error_code: str = "PAYMENT_ERROR"
    ):
        super().__init__(message, error_code, details, 400)


class PaymentDeclinedError(PaymentError):
    """Raised when a payment is declined."""

    def __init__(self, message: str = "Payment method declined", details: Optional[dict] = None):
        super().__init__(message, details, "PAYMENT_DECLINED")


class InsufficientFundsError(PaymentError):
    """Raised when there are insufficient funds."""

    def __init__(self, message: str = "Insufficient funds", details: Optional[dict] = None):
        super().__init__(message, details, "INSUFFICIENT_FUNDS")


class InventoryError(EcommerceMCPError):
    """Raised for inventory-related errors."""

    def __init__(
        self, message: str, details: Optional[dict] = None, error_code: str = "INVENTORY_ERROR"
    ):
        super().__init__(message, error_code, details, 400)


class NotFoundError(EcommerceMCPError):
    """Raised when resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(message, "NOT_FOUND", details, 404)


class ConflictError(EcommerceMCPError):
    """Raised for conflicts (e.g., duplicate SKU)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFLICT", details, 409)


class RateLimitError(EcommerceMCPError):
    """Raised when rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[dict] = None,
        retry_after: Optional[int] = None,
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details, 429)


class TimeoutError(EcommerceMCPError):
    """Raised when request times out."""

    def __init__(self, message: str = "Request timeout", details: Optional[dict] = None):
        super().__init__(message, "TIMEOUT", details, 504)


class ServiceUnavailableError(EcommerceMCPError):
    """Raised when backend service is unavailable."""

    def __init__(
        self, message: str = "Service unavailable", details: Optional[dict] = None
    ):
        super().__init__(message, "SERVICE_UNAVAILABLE", details, 503)


class ClientError(EcommerceMCPError):
    """Raised for client-side errors (4xx)."""

    def __init__(self, message: str, error_code: str, details: Optional[dict] = None):
        super().__init__(message, error_code, details, 400)


class ServerError(EcommerceMCPError):
    """Raised for server-side errors (5xx)."""

    def __init__(self, message: str, error_code: str, details: Optional[dict] = None):
        super().__init__(message, error_code, details, 500)

"""Payment processing and management tools."""

import logging
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    PaymentSchema,
    RefundSchema,
    ValidationError,
    format_success_response,
    format_error_response,
    format_transaction_response,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

payment_mcp = FastMCP(name="Payment Tools")


@payment_mcp.tool
async def process_payment(
    order_id: str,
    amount: float,
    currency: str,
    payment_method: str,
    payment_details: dict,
    idempotency_key: str = None,
) -> dict:
    """Process a payment transaction for an order.

    Args:
        order_id: Order identifier
        amount: Payment amount (must be > 0)
        currency: ISO 4217 currency code (USD, EUR, GBP, etc.)
        payment_method: One of: credit_card, debit_card, wallet, bank_transfer
        payment_details: Method-specific details (tokenized card, account info, etc.)
        idempotency_key: Unique key for idempotent retry safety

    Returns:
        dict with transaction_id, status, amount, currency, timestamp, confirmation_code

    Raises:
        ValidationError: If input validation fails
        PaymentDeclinedError: If payment method declined
        InsufficientFundsError: If insufficient funds
        TimeoutError: If payment processor timeout
    """
    if not settings.feature_payments:
        raise ValidationError("Payment feature is disabled", error_code="FEATURE_DISABLED")

    try:
        # Validate input
        from decimal import Decimal
        payment_data = PaymentSchema(
            order_id=order_id,
            amount=Decimal(str(amount)),
            currency=currency,
            payment_method=payment_method,
            payment_details=payment_details,
            idempotency_key=idempotency_key,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "payment"})

    try:
        # Make request to backend
        result = await api_client.post(
            "/api/v1/payments/process",
            data={
                "order_id": payment_data.order_id,
                "amount": float(payment_data.amount),
                "currency": payment_data.currency,
                "payment_method": payment_data.payment_method,
                "payment_details": payment_data.payment_details,
                "idempotency_key": payment_data.idempotency_key,
            },
            timeout=settings.payment_timeout,
        )

        logger.info(f"Payment processed: {result.get('transaction_id')} for order {order_id}")
        return result
    except Exception as e:
        logger.error(f"Payment processing failed for order {order_id}: {str(e)}")
        raise


@payment_mcp.tool
async def get_payment_status(transaction_id: str) -> dict:
    """Check the status of a payment transaction.

    Args:
        transaction_id: Transaction identifier

    Returns:
        dict with status, amount, method, order_id, timestamp, error_message (if applicable)

    Raises:
        ValidationError: If transaction_id is invalid
        NotFoundError: If transaction not found
    """
    if not transaction_id or not isinstance(transaction_id, str):
        raise ValidationError("transaction_id must be a non-empty string")

    try:
        result = await api_client.get(
            f"/api/v1/payments/{transaction_id}",
            cache=True,
            timeout=settings.payment_timeout,
        )

        logger.info(f"Payment status retrieved: {transaction_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to get payment status for {transaction_id}: {str(e)}")
        raise


@payment_mcp.tool
async def refund_payment(
    transaction_id: str,
    amount: float = None,
    reason: str = "customer_request",
    notes: str = None,
) -> dict:
    """Initiate a refund for a completed payment.

    Args:
        transaction_id: Original transaction ID
        amount: Partial refund amount in base currency (full refund if omitted)
        reason: Refund reason (customer_request, defective_item, duplicate_charge, fraud, other)
        notes: Additional notes about the refund

    Returns:
        dict with refund_id, status, amount, timestamp

    Raises:
        ValidationError: If input validation fails
        PaymentError: If refund cannot be processed
        NotFoundError: If transaction not found
    """
    if not settings.feature_payments:
        raise ValidationError("Payment feature is disabled", error_code="FEATURE_DISABLED")

    try:
        # Validate input
        from decimal import Decimal
        refund_data = RefundSchema(
            transaction_id=transaction_id,
            amount=Decimal(str(amount)) if amount else None,
            reason=reason,
            notes=notes,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "refund"})

    try:
        result = await api_client.post(
            f"/api/v1/payments/{refund_data.transaction_id}/refund",
            data={
                "amount": float(refund_data.amount) if refund_data.amount else None,
                "reason": refund_data.reason,
                "notes": refund_data.notes,
            },
            timeout=settings.payment_timeout,
        )

        logger.info(f"Refund initiated: {result.get('refund_id')} for transaction {transaction_id}")
        return result
    except Exception as e:
        logger.error(f"Refund failed for transaction {transaction_id}: {str(e)}")
        raise


@payment_mcp.tool
async def list_payment_methods(
    customer_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Retrieve all payment methods for a customer.

    Args:
        customer_id: Customer identifier
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of payment methods and pagination info
        Each method contains: method_id, type, last_four, expiry, is_default, created_at

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If customer not found
    """
    # Validate pagination parameters
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    if not customer_id or not isinstance(customer_id, str):
        raise ValidationError("customer_id must be a non-empty string")

    try:
        result = await api_client.get(
            f"/api/v1/customers/{customer_id}/payment-methods",
            params={"limit": limit, "offset": offset},
            cache=True,
        )

        logger.info(f"Payment methods retrieved for customer {customer_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to list payment methods for customer {customer_id}: {str(e)}")
        raise


@payment_mcp.tool
async def add_payment_method(
    customer_id: str,
    method_type: str,
    details: dict,
    set_as_default: bool = False,
) -> dict:
    """Add a new payment method to a customer profile.

    Args:
        customer_id: Customer identifier
        method_type: Type (credit_card, debit_card, wallet, bank_account)
        details: Payment method details (tokenized card, bank info, etc.)
        set_as_default: Make this the default payment method

    Returns:
        dict with method_id, type, last_four, status

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If customer not found
        ConflictError: If payment method already exists
    """
    if not settings.feature_payments:
        raise ValidationError("Payment feature is disabled", error_code="FEATURE_DISABLED")

    # Validate inputs
    if not customer_id or not isinstance(customer_id, str):
        raise ValidationError("customer_id must be a non-empty string")

    valid_types = ["credit_card", "debit_card", "wallet", "bank_account"]
    if method_type not in valid_types:
        raise ValidationError(f"method_type must be one of: {', '.join(valid_types)}")

    if not details or not isinstance(details, dict):
        raise ValidationError("details must be a non-empty dict")

    try:
        result = await api_client.post(
            f"/api/v1/customers/{customer_id}/payment-methods",
            data={
                "method_type": method_type,
                "details": details,
                "set_as_default": set_as_default,
            },
        )

        logger.info(f"Payment method added for customer {customer_id}: {result.get('method_id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to add payment method for customer {customer_id}: {str(e)}")
        raise

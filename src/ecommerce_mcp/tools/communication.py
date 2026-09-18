"""Customer communication and notification tools."""

import logging
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    EmailSchema,
    ContactPreferencesSchema,
    ValidationError,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

communication_mcp = FastMCP(name="Communication Tools")


@communication_mcp.tool
async def send_customer_email(
    customer_id: str,
    email_type: str,
    subject: str,
    body: str,
    template_id: Optional[str] = None,
    template_variables: Optional[Dict[str, Any]] = None,
) -> dict:
    """Send email notification to customer.

    Args:
        customer_id: Recipient customer ID
        email_type: Type (order_confirmation, shipment_notification, review_request,
                   promotional, support_response)
        subject: Email subject
        body: Email body (supports markdown)
        template_id: Use pre-built template
        template_variables: Variables for template

    Returns:
        dict with email_id, sent_to, status, timestamp

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If customer not found
    """
    if not settings.feature_communication:
        raise ValidationError("Communication feature is disabled", error_code="FEATURE_DISABLED")

    try:
        email_data = EmailSchema(
            customer_id=customer_id,
            email_type=email_type,
            subject=subject,
            body=body,
            template_id=template_id,
            template_variables=template_variables,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "email"})

    try:
        result = await api_client.post(
            "/api/v1/communications/email",
            data={
                "customer_id": email_data.customer_id,
                "email_type": email_data.email_type,
                "subject": email_data.subject,
                "body": email_data.body,
                "template_id": email_data.template_id,
                "template_variables": email_data.template_variables,
            },
        )

        logger.info(f"Email sent: {result.get('email_id')} to customer {customer_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email to customer {customer_id}: {str(e)}")
        raise


@communication_mcp.tool
async def list_customer_notifications(
    customer_id: str,
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Retrieve customer's notification history.

    Args:
        customer_id: Customer identifier
        notification_type: Filter by type (email, sms, push, in_app)
        status: Filter by status (sent, delivered, opened, clicked, bounced)
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of notifications and pagination info
        Each notification contains: notification_id, type, subject, sent_at, status, opened_at

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If customer not found
    """
    if not settings.feature_communication:
        raise ValidationError("Communication feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    if not customer_id or not isinstance(customer_id, str):
        raise ValidationError("customer_id must be a non-empty string")

    # Validate notification_type if provided
    valid_types = ["email", "sms", "push", "in_app"]
    if notification_type and notification_type not in valid_types:
        raise ValidationError(f"notification_type must be one of: {', '.join(valid_types)}")

    # Validate status if provided
    valid_statuses = ["sent", "delivered", "opened", "clicked", "bounced"]
    if status and status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}")

    params = {"limit": limit, "offset": offset}
    if notification_type:
        params["notification_type"] = notification_type
    if status:
        params["status"] = status

    try:
        result = await api_client.get(
            f"/api/v1/customers/{customer_id}/notifications",
            params=params,
            cache=True,
        )

        logger.info(f"Notifications retrieved: customer={customer_id}, count={len(result.get('data', []))}")
        return result
    except Exception as e:
        logger.error(f"Failed to list notifications for customer {customer_id}: {str(e)}")
        raise


@communication_mcp.tool
async def update_contact_preferences(
    customer_id: str,
    email_promotional: Optional[bool] = None,
    email_updates: Optional[bool] = None,
    sms_notifications: Optional[bool] = None,
    push_notifications: Optional[bool] = None,
    frequency: Optional[str] = None,
) -> dict:
    """Update customer's communication preferences.

    Args:
        customer_id: Customer identifier
        email_promotional: Receive promotional emails
        email_updates: Receive order/shipping updates
        sms_notifications: Receive SMS notifications
        push_notifications: Receive push notifications
        frequency: Preference frequency (daily, weekly, monthly)

    Returns:
        dict with customer_id, preferences_updated, timestamp

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If customer not found
    """
    if not settings.feature_communication:
        raise ValidationError("Communication feature is disabled", error_code="FEATURE_DISABLED")

    try:
        preferences_data = ContactPreferencesSchema(
            customer_id=customer_id,
            email_promotional=email_promotional,
            email_updates=email_updates,
            sms_notifications=sms_notifications,
            push_notifications=push_notifications,
            frequency=frequency,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "preferences"})

    try:
        result = await api_client.put(
            f"/api/v1/customers/{customer_id}/preferences",
            data={
                "email_promotional": preferences_data.email_promotional,
                "email_updates": preferences_data.email_updates,
                "sms_notifications": preferences_data.sms_notifications,
                "push_notifications": preferences_data.push_notifications,
                "frequency": preferences_data.frequency,
            },
        )

        logger.info(f"Contact preferences updated: customer={customer_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to update preferences for customer {customer_id}: {str(e)}")
        raise

"""Analytics and reporting tools."""

import logging
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    SalesMetricsSchema,
    ExportReportSchema,
    ValidationError,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

analytics_mcp = FastMCP(name="Analytics Tools")


@analytics_mcp.tool
async def get_sales_metrics(
    period: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    breakdown_by: Optional[str] = None,
) -> dict:
    """Retrieve sales performance metrics.

    Args:
        period: Time period (today, week, month, quarter, year, custom)
        start_date: Start date for custom period (ISO format)
        end_date: End date for custom period (ISO format)
        breakdown_by: Breakdown dimension (category, product, customer_tier, region)

    Returns:
        dict with total_revenue, order_count, average_order_value, top_products,
        top_categories, metrics_by_dimension (if breakdown specified), growth_rate

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_analytics:
        raise ValidationError("Analytics feature is disabled", error_code="FEATURE_DISABLED")

    try:
        from datetime import datetime

        metrics_data = SalesMetricsSchema(
            period=period,
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            breakdown_by=breakdown_by,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "metrics"})

    params = {"period": metrics_data.period}
    if metrics_data.start_date:
        params["start_date"] = metrics_data.start_date.isoformat()
    if metrics_data.end_date:
        params["end_date"] = metrics_data.end_date.isoformat()
    if metrics_data.breakdown_by:
        params["breakdown_by"] = metrics_data.breakdown_by

    try:
        result = await api_client.get(
            "/api/v1/analytics/sales",
            params=params,
            cache=True,
        )

        logger.info(f"Sales metrics retrieved: period={period}, revenue={result.get('total_revenue')}")
        return result
    except Exception as e:
        logger.error(f"Failed to get sales metrics: {str(e)}")
        raise


@analytics_mcp.tool
async def get_customer_analytics(
    period: str,
    include_segments: bool = False,
    include_churn: bool = False,
) -> dict:
    """Retrieve customer insights and behavior metrics.

    Args:
        period: Time period (month, quarter, year)
        include_segments: Include customer segmentation
        include_churn: Include churn analysis

    Returns:
        dict with new_customers, repeat_customers, customer_lifetime_value,
        retention_rate, churn_rate, segments (if requested), cohort_data

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_analytics:
        raise ValidationError("Analytics feature is disabled", error_code="FEATURE_DISABLED")

    # Validate period
    valid_periods = ["month", "quarter", "year"]
    if period not in valid_periods:
        raise ValidationError(f"period must be one of: {', '.join(valid_periods)}")

    params = {
        "period": period,
        "include_segments": include_segments,
        "include_churn": include_churn,
    }

    try:
        result = await api_client.get(
            "/api/v1/analytics/customers",
            params=params,
            cache=True,
        )

        logger.info(f"Customer analytics retrieved: period={period}")
        return result
    except Exception as e:
        logger.error(f"Failed to get customer analytics: {str(e)}")
        raise


@analytics_mcp.tool
async def export_report(
    report_type: str,
    format: str,
    period: str,
    filters: Optional[Dict[str, Any]] = None,
) -> dict:
    """Generate and export report in CSV or PDF format.

    Args:
        report_type: Type (sales, inventory, customers, orders, reviews)
        format: Export format (csv, pdf, json)
        period: Time period (week, month, quarter, year)
        filters: Additional filtering criteria

    Returns:
        dict with report_id, file_url, file_size, generated_at, expires_at

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_analytics:
        raise ValidationError("Analytics feature is disabled", error_code="FEATURE_DISABLED")

    try:
        report_data = ExportReportSchema(
            report_type=report_type,
            format=format,
            period=period,
            filters=filters,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "report"})

    try:
        result = await api_client.post(
            "/api/v1/analytics/export",
            data={
                "report_type": report_data.report_type,
                "format": report_data.format,
                "period": report_data.period,
                "filters": report_data.filters,
            },
        )

        logger.info(f"Report exported: {result.get('report_id')} ({report_type}, {format})")
        return result
    except Exception as e:
        logger.error(f"Failed to export report: {str(e)}")
        raise

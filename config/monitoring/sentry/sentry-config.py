"""
Sentry Configuration and Integration
Enhanced error tracking with release management, performance monitoring, and custom context
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
import os
import logging


def configure_sentry():
    """
    Configure Sentry SDK with comprehensive integrations and settings
    """
    environment = os.getenv("ENVIRONMENT", "development")
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logging.warning("SENTRY_DSN not configured - error tracking disabled")
        return

    # Configure integrations
    integrations = [
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes=[500, 501, 502, 503, 504, 505]
        ),
        SqlalchemyIntegration(),
        RedisIntegration(),
        CeleryIntegration(
            monitor_beat_tasks=True,
            exclude_beat_tasks=[]
        ),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        ),
        AsyncioIntegration()
    ]

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=integrations,
        environment=environment,
        release=os.getenv("RELEASE_VERSION", "unknown"),

        # Performance monitoring
        traces_sample_rate=get_traces_sample_rate(environment),
        profiles_sample_rate=get_profiles_sample_rate(environment),

        # Error sampling
        sample_rate=1.0,  # Capture 100% of errors

        # Request data
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=100,
        attach_stacktrace=True,

        # Performance tuning
        max_request_body_size="medium",  # "small", "medium", "large", "always"

        # Before send hook for filtering
        before_send=before_send_handler,
        before_breadcrumb=before_breadcrumb_handler,

        # Context
        debug=environment == "development",
    )

    logging.info(f"Sentry configured for environment: {environment}")


def get_traces_sample_rate(environment: str) -> float:
    """
    Get traces sample rate based on environment

    Args:
        environment: Current environment name

    Returns:
        Sample rate between 0.0 and 1.0
    """
    rates = {
        "production": 0.1,   # 10% sampling in production
        "staging": 0.5,      # 50% sampling in staging
        "development": 1.0   # 100% sampling in development
    }
    return rates.get(environment, 0.1)


def get_profiles_sample_rate(environment: str) -> float:
    """
    Get profiling sample rate based on environment

    Args:
        environment: Current environment name

    Returns:
        Sample rate between 0.0 and 1.0
    """
    rates = {
        "production": 0.05,  # 5% profiling in production
        "staging": 0.2,      # 20% profiling in staging
        "development": 0.5   # 50% profiling in development
    }
    return rates.get(environment, 0.05)


def before_send_handler(event, hint):
    """
    Filter and enrich events before sending to Sentry

    Args:
        event: Sentry event dictionary
        hint: Additional information about the event

    Returns:
        Modified event or None to drop the event
    """
    # Drop health check errors
    if event.get("request", {}).get("url", "").endswith("/health"):
        return None

    # Drop expected errors
    if event.get("exception"):
        values = event["exception"].get("values", [])
        for value in values:
            error_type = value.get("type", "")

            # Drop specific error types
            if error_type in ["ValidationError", "HTTPException"]:
                return None

            # Drop errors from specific modules
            module = value.get("module", "")
            if module.startswith("tests."):
                return None

    # Add custom context
    event.setdefault("contexts", {})
    event["contexts"]["application"] = {
        "name": "SEC Latent Analysis",
        "version": os.getenv("RELEASE_VERSION", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

    # Add user context (without PII)
    if "user" in event:
        event["user"] = {
            "id": event["user"].get("id"),
            "role": event["user"].get("role")
        }

    return event


def before_breadcrumb_handler(crumb, hint):
    """
    Filter and enrich breadcrumbs before adding to event

    Args:
        crumb: Breadcrumb dictionary
        hint: Additional information

    Returns:
        Modified breadcrumb or None to drop
    """
    # Drop noisy breadcrumbs
    if crumb.get("category") == "query" and crumb.get("message", "").startswith("SELECT 1"):
        return None

    # Limit breadcrumb message length
    if "message" in crumb:
        crumb["message"] = crumb["message"][:500]

    return crumb


def set_user_context(user_id: str, role: str = None):
    """
    Set user context for Sentry events

    Args:
        user_id: User identifier
        role: User role
    """
    sentry_sdk.set_user({
        "id": user_id,
        "role": role
    })


def set_request_context(request_id: str, endpoint: str = None):
    """
    Set request context for Sentry events

    Args:
        request_id: Unique request identifier
        endpoint: API endpoint being accessed
    """
    sentry_sdk.set_context("request", {
        "request_id": request_id,
        "endpoint": endpoint
    })


def set_business_context(filing_id: str = None, company: str = None):
    """
    Set business context for Sentry events

    Args:
        filing_id: SEC filing identifier
        company: Company name or ticker
    """
    sentry_sdk.set_context("business", {
        "filing_id": filing_id,
        "company": company
    })


def capture_exception_with_context(exception: Exception, **context):
    """
    Capture exception with additional context

    Args:
        exception: Exception to capture
        **context: Additional context key-value pairs
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def capture_message_with_context(message: str, level: str = "info", **context):
    """
    Capture message with additional context

    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error, fatal)
        **context: Additional context key-value pairs
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def start_transaction(name: str, op: str = "http.server"):
    """
    Start a performance transaction

    Args:
        name: Transaction name
        op: Operation type

    Returns:
        Transaction context manager
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def create_check_in(monitor_slug: str, status: str = "in_progress"):
    """
    Create Sentry Cron Monitor check-in

    Args:
        monitor_slug: Monitor identifier
        status: Check-in status (in_progress, ok, error)

    Returns:
        Check-in ID
    """
    return sentry_sdk.api.crons.capture_checkin(
        monitor_slug=monitor_slug,
        status=status
    )


# Middleware for FastAPI
class SentryMiddleware:
    """
    FastAPI middleware for Sentry integration
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Set request context
            request_id = scope.get("headers", {}).get("x-request-id", "unknown")
            set_request_context(request_id, scope.get("path"))

        await self.app(scope, receive, send)

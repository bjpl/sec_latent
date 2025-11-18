"""
Sentry Error Tracking Integration
Comprehensive error monitoring and performance tracking
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging
import os


def init_sentry(
    dsn: str = None,
    environment: str = "production",
    release: str = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
):
    """
    Initialize Sentry SDK with comprehensive integrations

    Args:
        dsn: Sentry DSN (required)
        environment: Deployment environment
        release: Application version/release tag
        traces_sample_rate: Performance monitoring sample rate (0.0-1.0)
        profiles_sample_rate: Profiling sample rate (0.0-1.0)
    """
    if not dsn:
        dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        logging.warning("Sentry DSN not configured. Error tracking disabled.")
        return

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    # Initialize Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release or os.getenv("VERSION", "unknown"),
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[403, range(500, 599)]
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                exclude_beat_tasks=[]
            ),
            RedisIntegration(),
            SqlalchemyIntegration(),
            logging_integration,
        ],

        # Performance Monitoring
        traces_sample_rate=traces_sample_rate,

        # Profiling
        profiles_sample_rate=profiles_sample_rate,

        # Set traces_sampler for custom sampling logic
        # traces_sampler=traces_sampler_function,

        # Send default PII (Personally Identifiable Information)
        send_default_pii=False,

        # Attach stack trace to messages
        attach_stacktrace=True,

        # Maximum breadcrumbs
        max_breadcrumbs=50,

        # Debug mode
        debug=False,

        # Before send hook for filtering/modifying events
        before_send=before_send_hook,

        # Before breadcrumb hook
        before_breadcrumb=before_breadcrumb_hook,
    )

    logging.info(f"Sentry initialized for environment: {environment}")


def before_send_hook(event, hint):
    """
    Filter or modify events before sending to Sentry

    Args:
        event: Event data
        hint: Additional context

    Returns:
        Modified event or None to drop the event
    """
    # Filter out specific errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Don't send certain exceptions
        ignored_exceptions = [
            'ConnectionAbortedError',
            'asyncio.CancelledError',
        ]

        if exc_type.__name__ in ignored_exceptions:
            return None

    # Add custom context
    if 'request' in event:
        event.setdefault('tags', {})
        event['tags']['api_version'] = 'v1'

    # Sanitize sensitive data
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[Filtered]'

    return event


def before_breadcrumb_hook(crumb, hint):
    """
    Filter or modify breadcrumbs before adding to event

    Args:
        crumb: Breadcrumb data
        hint: Additional context

    Returns:
        Modified breadcrumb or None to drop it
    """
    # Filter out noisy breadcrumbs
    if crumb.get('category') == 'httplib':
        return None

    # Sanitize query parameters
    if crumb.get('category') == 'query':
        if 'data' in crumb:
            crumb['data'] = '[Filtered]'

    return crumb


def capture_custom_event(
    message: str,
    level: str = "info",
    extra: dict = None,
    tags: dict = None,
    user: dict = None,
    fingerprint: list = None
):
    """
    Capture custom event with additional context

    Args:
        message: Event message
        level: Severity level (debug, info, warning, error, fatal)
        extra: Extra context data
        tags: Event tags
        user: User information
        fingerprint: Custom fingerprint for grouping
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if user:
            scope.set_user(user)

        if fingerprint:
            scope.fingerprint = fingerprint

        scope.level = level
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str, email: str = None, username: str = None):
    """Set user context for error tracking"""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def set_custom_context(name: str, data: dict):
    """Set custom context for additional debugging information"""
    sentry_sdk.set_context(name, data)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict = None
):
    """Add custom breadcrumb for tracking user actions"""
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


# Example usage in FastAPI app
"""
from config.monitoring.sentry import sentry_init

# Initialize at startup
@app.on_event("startup")
async def startup_event():
    init_sentry(
        environment=os.getenv("ENVIRONMENT", "development"),
        traces_sample_rate=0.1 if os.getenv("ENVIRONMENT") == "production" else 1.0
    )

# Use in endpoints
@app.get("/api/example")
async def example_endpoint():
    try:
        # Add breadcrumb
        add_breadcrumb("Processing example request", category="api")

        # Set custom context
        set_custom_context("business_logic", {
            "operation": "example",
            "complexity": "low"
        })

        # Your code here
        result = process_data()

        return {"result": result}
    except Exception as e:
        # Capture exception with additional context
        capture_custom_event(
            message="Example processing failed",
            level="error",
            extra={"error": str(e)},
            tags={"endpoint": "example"}
        )
        raise
"""

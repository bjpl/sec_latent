"""
Audit Logging System
Structured logging for security events and compliance
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from fastapi import Request
import traceback


class AuditEventType(str, Enum):
    """Audit Event Types"""
    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_FAILED = "auth.failed"

    # Authorization events
    AUTHZ_GRANTED = "authz.granted"
    AUTHZ_DENIED = "authz.denied"

    # Data access events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"

    # API key events
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    API_KEY_ROTATED = "api_key.rotated"

    # Security events
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_IP_BLOCKED = "security.ip_blocked"

    # System events
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"


class AuditLevel(str, Enum):
    """Audit Event Severity Levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Structured Audit Event"""
    timestamp: datetime
    event_type: AuditEventType
    level: AuditLevel
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    status: str  # success, failure, blocked
    message: str
    details: Dict[str, Any] = {}
    request_id: Optional[str] = None
    trace_id: Optional[str] = None


class AuditLogger:
    """
    Centralized audit logging system with structured output
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        console_output: bool = True,
        json_format: bool = True
    ):
        """
        Initialize AuditLogger

        Args:
            log_file: Path to audit log file (optional)
            console_output: Enable console output
            json_format: Use JSON format for logs
        """
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.json_format = json_format

        # Clear existing handlers
        self.logger.handlers = []

        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            if json_format:
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(file_handler)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            if json_format:
                console_handler.setFormatter(JsonFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(console_handler)

    def log_event(self, event: AuditEvent):
        """
        Log audit event

        Args:
            event: AuditEvent to log
        """
        level_map = {
            AuditLevel.DEBUG: logging.DEBUG,
            AuditLevel.INFO: logging.INFO,
            AuditLevel.WARNING: logging.WARNING,
            AuditLevel.ERROR: logging.ERROR,
            AuditLevel.CRITICAL: logging.CRITICAL
        }

        log_level = level_map.get(event.level, logging.INFO)

        if self.json_format:
            log_data = event.dict()
            log_data['timestamp'] = log_data['timestamp'].isoformat()
            self.logger.log(log_level, json.dumps(log_data))
        else:
            self.logger.log(log_level, event.message, extra=event.dict())

    def log_authentication(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """
        Log authentication event

        Args:
            user_id: User identifier
            success: Whether authentication succeeded
            ip_address: Client IP address
            details: Additional details
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED,
            level=AuditLevel.INFO if success else AuditLevel.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            status="success" if success else "failure",
            message=f"User authentication {'succeeded' if success else 'failed'}",
            details=details or {}
        )
        self.log_event(event)

    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        required_permissions: list[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log authorization event

        Args:
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed
            granted: Whether access was granted
            required_permissions: Required permissions
            ip_address: Client IP address
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.AUTHZ_GRANTED if granted else AuditEventType.AUTHZ_DENIED,
            level=AuditLevel.INFO if granted else AuditLevel.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            status="granted" if granted else "denied",
            message=f"Access {'granted' if granted else 'denied'} to {resource}",
            details={
                "required_permissions": required_permissions or []
            }
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """
        Log data access event

        Args:
            user_id: User identifier
            resource: Resource being accessed
            action: Action (read, write, delete)
            success: Whether action succeeded
            details: Additional details
        """
        event_type_map = {
            "read": AuditEventType.DATA_READ,
            "write": AuditEventType.DATA_WRITE,
            "delete": AuditEventType.DATA_DELETE
        }

        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type_map.get(action.lower(), AuditEventType.DATA_READ),
            level=AuditLevel.INFO,
            user_id=user_id,
            resource=resource,
            action=action,
            status="success" if success else "failure",
            message=f"Data {action} on {resource}",
            details=details or {}
        )
        self.log_event(event)

    def log_api_key_event(
        self,
        event_type: str,
        key_id: str,
        user_id: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """
        Log API key lifecycle event

        Args:
            event_type: Event type (created, revoked, rotated)
            key_id: API key identifier
            user_id: User who performed action
            details: Additional details
        """
        event_type_map = {
            "created": AuditEventType.API_KEY_CREATED,
            "revoked": AuditEventType.API_KEY_REVOKED,
            "rotated": AuditEventType.API_KEY_ROTATED
        }

        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type_map.get(event_type, AuditEventType.API_KEY_CREATED),
            level=AuditLevel.INFO,
            user_id=user_id,
            resource=f"api_key:{key_id}",
            action=event_type,
            status="success",
            message=f"API key {event_type}: {key_id}",
            details=details or {}
        )
        self.log_event(event)

    def log_security_event(
        self,
        event_type: AuditEventType,
        message: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """
        Log security-related event

        Args:
            event_type: Security event type
            message: Event description
            ip_address: Client IP address
            user_id: User identifier (if known)
            details: Additional details
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            level=AuditLevel.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            status="blocked",
            message=message,
            details=details or {}
        )
        self.log_event(event)

    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log error event

        Args:
            message: Error message
            exception: Exception object
            user_id: User identifier
            request_id: Request identifier
        """
        details = {}
        if exception:
            details['exception_type'] = type(exception).__name__
            details['exception_message'] = str(exception)
            details['traceback'] = traceback.format_exc()

        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.SYSTEM_ERROR,
            level=AuditLevel.ERROR,
            user_id=user_id,
            request_id=request_id,
            status="error",
            message=message,
            details=details
        )
        self.log_event(event)

    def log_request(
        self,
        request: Request,
        user_id: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: Optional[float] = None
    ):
        """
        Log HTTP request

        Args:
            request: FastAPI request object
            user_id: Authenticated user ID
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
        """
        details = {
            "method": request.method,
            "url": str(request.url),
            "status_code": status_code,
            "user_agent": request.headers.get("user-agent"),
        }

        if response_time_ms:
            details["response_time_ms"] = response_time_ms

        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.DATA_READ,
            level=AuditLevel.INFO,
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            resource=str(request.url.path),
            action=request.method,
            status="success" if status_code < 400 else "failure",
            message=f"{request.method} {request.url.path} - {status_code}",
            details=details
        )
        self.log_event(event)


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'resource'):
            log_data['resource'] = record.resource

        return json.dumps(log_data)

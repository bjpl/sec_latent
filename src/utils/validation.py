"""
Input Validation and Sanitization
Prevents injection attacks and validates user input
"""

import re
from typing import Any, Optional, List
from pydantic import BaseModel, validator, Field
from html import escape
import unicodedata
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputSanitizer:
    """
    Input sanitization utilities
    """

    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(;.*)",
        r"(\bUNION\b.*\bSELECT\b)"
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\$\{.*\}",
        r"\$\(.*\)"
    ]

    @staticmethod
    def sanitize_string(
        value: str,
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """
        Sanitize string input

        Args:
            value: Input string
            max_length: Maximum allowed length
            allow_html: Allow HTML tags (escaped)
            strip_whitespace: Strip leading/trailing whitespace

        Returns:
            Sanitized string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Strip whitespace
        if strip_whitespace:
            value = value.strip()

        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(f"String too long (max {max_length} characters)")

        # Normalize unicode
        value = unicodedata.normalize('NFKC', value)

        # Escape HTML if not allowed
        if not allow_html:
            value = escape(value)

        # Check for XSS patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS pattern detected in input: {pattern}")
                raise ValidationError("Potentially dangerous content detected")

        return value

    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Sanitize input for SQL (though parameterized queries are preferred)

        Args:
            value: Input string

        Returns:
            Sanitized string

        Raises:
            ValidationError: If SQL injection patterns detected
        """
        # Check for SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                raise ValidationError("Potentially dangerous SQL content detected")

        # Escape single quotes
        value = value.replace("'", "''")

        return value

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal

        Args:
            filename: Input filename

        Returns:
            Sanitized filename

        Raises:
            ValidationError: If filename is invalid
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Remove leading dots
        filename = filename.lstrip('.')

        # Check for empty result
        if not filename:
            raise ValidationError("Invalid filename")

        # Only allow alphanumeric, dash, underscore, dot
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            raise ValidationError("Filename contains invalid characters")

        return filename

    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Validate and sanitize email address

        Args:
            email: Email address

        Returns:
            Sanitized email

        Raises:
            ValidationError: If email is invalid
        """
        # Basic email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            raise ValidationError("Invalid email address")

        return email.lower().strip()

    @staticmethod
    def sanitize_url(url: str, allowed_schemes: List[str] = None) -> str:
        """
        Validate and sanitize URL

        Args:
            url: URL to validate
            allowed_schemes: Allowed URL schemes (default: http, https)

        Returns:
            Sanitized URL

        Raises:
            ValidationError: If URL is invalid
        """
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']

        # Basic URL pattern
        pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'

        if not re.match(pattern, url, re.IGNORECASE):
            raise ValidationError("Invalid URL format")

        # Check scheme
        scheme = url.split('://')[0].lower()
        if scheme not in allowed_schemes:
            raise ValidationError(f"URL scheme not allowed: {scheme}")

        # Check for javascript: or data: URIs
        if re.search(r'(javascript|data):', url, re.IGNORECASE):
            raise ValidationError("Potentially dangerous URL detected")

        return url

    @staticmethod
    def sanitize_integer(
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> int:
        """
        Validate and convert to integer

        Args:
            value: Input value
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Integer value

        Raises:
            ValidationError: If conversion or validation fails
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid integer value")

        if min_value is not None and int_value < min_value:
            raise ValidationError(f"Value too small (min: {min_value})")

        if max_value is not None and int_value > max_value:
            raise ValidationError(f"Value too large (max: {max_value})")

        return int_value

    @staticmethod
    def sanitize_float(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """
        Validate and convert to float

        Args:
            value: Input value
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Float value

        Raises:
            ValidationError: If conversion or validation fails
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid float value")

        if min_value is not None and float_value < min_value:
            raise ValidationError(f"Value too small (min: {min_value})")

        if max_value is not None and float_value > max_value:
            raise ValidationError(f"Value too large (max: {max_value})")

        return float_value


class SecureString(BaseModel):
    """Validated string field"""
    value: str = Field(..., min_length=1, max_length=1000)

    @validator('value')
    def sanitize_value(cls, v):
        return InputSanitizer.sanitize_string(v)


class SecureEmail(BaseModel):
    """Validated email field"""
    value: str

    @validator('value')
    def sanitize_email(cls, v):
        return InputSanitizer.sanitize_email(v)


class SecureURL(BaseModel):
    """Validated URL field"""
    value: str

    @validator('value')
    def sanitize_url(cls, v):
        return InputSanitizer.sanitize_url(v)


class SecureFilename(BaseModel):
    """Validated filename field"""
    value: str = Field(..., min_length=1, max_length=255)

    @validator('value')
    def sanitize_filename(cls, v):
        return InputSanitizer.sanitize_filename(v)


def validate_json_structure(data: dict, required_fields: List[str]) -> bool:
    """
    Validate JSON structure has required fields

    Args:
        data: JSON data dictionary
        required_fields: List of required field names

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return True


def sanitize_dict(
    data: dict,
    allowed_keys: Optional[List[str]] = None,
    max_depth: int = 10,
    current_depth: int = 0
) -> dict:
    """
    Sanitize dictionary recursively

    Args:
        data: Dictionary to sanitize
        allowed_keys: Whitelist of allowed keys (None = allow all)
        max_depth: Maximum nesting depth
        current_depth: Current recursion depth

    Returns:
        Sanitized dictionary

    Raises:
        ValidationError: If validation fails
    """
    if current_depth > max_depth:
        raise ValidationError("Dictionary nesting too deep")

    sanitized = {}

    for key, value in data.items():
        # Check allowed keys
        if allowed_keys is not None and key not in allowed_keys:
            logger.warning(f"Unexpected key in input: {key}")
            continue

        # Sanitize key
        if not isinstance(key, str):
            raise ValidationError("Dictionary keys must be strings")

        clean_key = InputSanitizer.sanitize_string(key, max_length=100)

        # Sanitize value
        if isinstance(value, dict):
            sanitized[clean_key] = sanitize_dict(
                value,
                allowed_keys=None,
                max_depth=max_depth,
                current_depth=current_depth + 1
            )
        elif isinstance(value, str):
            sanitized[clean_key] = InputSanitizer.sanitize_string(value)
        elif isinstance(value, (int, float, bool, type(None))):
            sanitized[clean_key] = value
        elif isinstance(value, list):
            sanitized[clean_key] = [
                InputSanitizer.sanitize_string(str(item))
                if isinstance(item, str) else item
                for item in value
            ]
        else:
            logger.warning(f"Unsupported value type for key {key}: {type(value)}")

    return sanitized

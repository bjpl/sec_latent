"""
Security Headers Middleware
Implements security headers: CORS, CSP, HSTS, X-Frame-Options, etc.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """

    def __init__(
        self,
        app,
        # Content Security Policy
        csp_directives: Optional[dict] = None,
        # CORS
        cors_allow_origins: List[str] = None,
        cors_allow_credentials: bool = True,
        # HSTS
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        # Frame options
        frame_options: str = "DENY",  # DENY, SAMEORIGIN, or ALLOW-FROM
        # Other security headers
        content_type_options: bool = True,
        xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin"
    ):
        """
        Initialize SecurityHeadersMiddleware

        Args:
            app: FastAPI application
            csp_directives: Content Security Policy directives
            cors_allow_origins: Allowed CORS origins
            cors_allow_credentials: Allow credentials in CORS
            hsts_max_age: HSTS max age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            frame_options: X-Frame-Options value
            content_type_options: Enable X-Content-Type-Options: nosniff
            xss_protection: Enable X-XSS-Protection
            referrer_policy: Referrer-Policy value
        """
        super().__init__(app)

        # Content Security Policy
        if csp_directives is None:
            csp_directives = {
                "default-src": ["'self'"],
                "script-src": ["'self'", "'unsafe-inline'"],
                "style-src": ["'self'", "'unsafe-inline'"],
                "img-src": ["'self'", "data:", "https:"],
                "font-src": ["'self'", "data:"],
                "connect-src": ["'self'"],
                "frame-ancestors": ["'none'"],
                "base-uri": ["'self'"],
                "form-action": ["'self'"]
            }
        self.csp = self._build_csp(csp_directives)

        # CORS
        self.cors_origins = cors_allow_origins or ["*"]
        self.cors_credentials = cors_allow_credentials

        # HSTS
        hsts_parts = [f"max-age={hsts_max_age}"]
        if hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")
        if hsts_preload:
            hsts_parts.append("preload")
        self.hsts = "; ".join(hsts_parts)

        # Other headers
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy

        logger.info("SecurityHeadersMiddleware initialized")

    def _build_csp(self, directives: dict) -> str:
        """
        Build Content-Security-Policy header value from directives

        Args:
            directives: CSP directives dictionary

        Returns:
            CSP header value
        """
        parts = []
        for directive, sources in directives.items():
            if isinstance(sources, list):
                sources_str = " ".join(sources)
            else:
                sources_str = sources
            parts.append(f"{directive} {sources_str}")
        return "; ".join(parts)

    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Content Security Policy
        if self.csp:
            response.headers["Content-Security-Policy"] = self.csp

        # HSTS (only on HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.hsts

        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.frame_options

        # X-Content-Type-Options
        if self.content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (deprecated but still useful for older browsers)
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # Remove Server header (don't reveal server info)
        if "Server" in response.headers:
            del response.headers["Server"]

        # X-Powered-By (if exists, remove it)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security checks
    """

    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True,
        expose_headers: List[str] = None,
        max_age: int = 600
    ):
        """
        Initialize CORSSecurityMiddleware

        Args:
            app: FastAPI application
            allow_origins: Allowed origins (exact match or wildcard)
            allow_methods: Allowed HTTP methods
            allow_headers: Allowed request headers
            allow_credentials: Allow credentials
            expose_headers: Headers to expose to browser
            max_age: Preflight cache duration in seconds
        """
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed

        Args:
            origin: Request origin

        Returns:
            True if allowed
        """
        if "*" in self.allow_origins:
            return True

        return origin in self.allow_origins

    async def dispatch(self, request: Request, call_next):
        """
        Handle CORS preflight and add CORS headers

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response with CORS headers
        """
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin and self._is_origin_allowed(origin):
                response = Response(status_code=204)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
                return response
            else:
                logger.warning(f"CORS preflight rejected for origin: {origin}")
                return Response(status_code=403, content="Origin not allowed")

        # Process actual request
        response = await call_next(request)

        # Add CORS headers
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        return response

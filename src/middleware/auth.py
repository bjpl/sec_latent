"""
Authentication Middleware
JWT and API key authentication for FastAPI
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable
import logging
from datetime import datetime

from ..security.auth import TokenManager, JWTAuthenticator
from ..security.api_keys import APIKeyManager
from ..security.audit import AuditLogger

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT and API key authentication
    """

    def __init__(
        self,
        app,
        token_manager: TokenManager,
        api_key_manager: Optional[APIKeyManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        excluded_paths: list[str] = None
    ):
        """
        Initialize AuthenticationMiddleware

        Args:
            app: FastAPI application
            token_manager: TokenManager instance
            api_key_manager: Optional APIKeyManager for API key auth
            audit_logger: Optional AuditLogger for audit logging
            excluded_paths: Paths to exclude from authentication
        """
        super().__init__(app)
        self.token_manager = token_manager
        self.api_key_manager = api_key_manager
        self.audit_logger = audit_logger
        self.jwt_authenticator = JWTAuthenticator(token_manager)

        # Default excluded paths
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request through authentication

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Track request start time
        start_time = datetime.utcnow()

        try:
            # Try JWT authentication first
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

                # Check if it's an API key or JWT
                if token.startswith("sk_"):
                    # API key authentication
                    if not self.api_key_manager:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key authentication not configured"
                        )

                    metadata = self.api_key_manager.validate_key(
                        token,
                        client_ip=request.client.host if request.client else None
                    )

                    if not metadata:
                        if self.audit_logger:
                            self.audit_logger.log_authentication(
                                user_id="unknown",
                                success=False,
                                ip_address=request.client.host if request.client else None,
                                details={"auth_type": "api_key"}
                            )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API key"
                        )

                    # Attach API key info to request state
                    request.state.auth_type = "api_key"
                    request.state.api_key_id = metadata.key_id
                    request.state.user_id = f"api_key:{metadata.key_id}"
                    request.state.scopes = metadata.scopes

                    if self.audit_logger:
                        self.audit_logger.log_authentication(
                            user_id=request.state.user_id,
                            success=True,
                            ip_address=request.client.host if request.client else None,
                            details={"auth_type": "api_key", "key_id": metadata.key_id}
                        )

                else:
                    # JWT authentication
                    payload = await self.jwt_authenticator(request)
                    request.state.auth_type = "jwt"

                    if self.audit_logger:
                        self.audit_logger.log_authentication(
                            user_id=payload.sub,
                            success=True,
                            ip_address=request.client.host if request.client else None,
                            details={"auth_type": "jwt"}
                        )

            else:
                # No authentication provided
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Process request
            response = await call_next(request)

            # Log successful request
            if self.audit_logger:
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.audit_logger.log_request(
                    request,
                    user_id=request.state.user_id,
                    status_code=response.status_code,
                    response_time_ms=response_time
                )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            if self.audit_logger:
                self.audit_logger.log_error(
                    message="Authentication middleware error",
                    exception=e,
                    user_id=getattr(request.state, 'user_id', None)
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )

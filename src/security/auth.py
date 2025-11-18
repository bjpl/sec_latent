"""
JWT Authentication System
Implements token generation, validation, and refresh mechanisms
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator
import logging
from functools import wraps
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT Token Payload Schema"""
    sub: str  # Subject (user_id)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    jti: str  # JWT ID (unique identifier)
    type: str  # Token type: 'access' or 'refresh'
    roles: list[str] = []
    permissions: list[str] = []

    @validator('type')
    def validate_type(cls, v):
        if v not in ['access', 'refresh']:
            raise ValueError('Token type must be "access" or "refresh"')
        return v


class TokenManager:
    """
    Manages JWT token lifecycle including generation, validation, and refresh
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """
        Initialize TokenManager

        Args:
            secret_key: Secret key for JWT signing (must be 32+ chars)
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration time
            refresh_token_expire_days: Refresh token expiration time
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)

        # Token blacklist (in-memory - use Redis in production)
        self._blacklist: set[str] = set()

        logger.info(f"TokenManager initialized with {algorithm} algorithm")

    def create_access_token(
        self,
        user_id: str,
        roles: list[str] = None,
        permissions: list[str] = None,
        extra_claims: Dict[str, Any] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: Unique user identifier
            roles: List of user roles
            permissions: List of user permissions
            extra_claims: Additional claims to include

        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        expires = now + self.access_token_expire

        payload = {
            "sub": user_id,
            "exp": int(expires.timestamp()),
            "iat": int(now.timestamp()),
            "jti": secrets.token_urlsafe(16),
            "type": "access",
            "roles": roles or [],
            "permissions": permissions or []
        }

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created access token for user {user_id}")
        return token

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: Unique user identifier

        Returns:
            Encoded JWT refresh token
        """
        now = datetime.utcnow()
        expires = now + self.refresh_token_expire

        payload = {
            "sub": user_id,
            "exp": int(expires.timestamp()),
            "iat": int(now.timestamp()),
            "jti": secrets.token_urlsafe(16),
            "type": "refresh"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created refresh token for user {user_id}")
        return token

    def verify_token(self, token: str, token_type: str = "access") -> TokenPayload:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid, expired, or blacklisted
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti in self._blacklist:
                logger.warning(f"Blacklisted token used: {jti}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            # Validate token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )

            return TokenPayload(**payload)

        except jwt.ExpiredSignatureError:
            logger.warning("Expired token used")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict with new access_token and optionally new refresh_token
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, token_type="refresh")

        # Create new access token
        access_token = self.create_access_token(
            user_id=payload.sub,
            roles=payload.roles,
            permissions=payload.permissions
        )

        logger.info(f"Refreshed access token for user {payload.sub}")

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    def revoke_token(self, token: str):
        """
        Revoke token by adding to blacklist

        Args:
            token: Token to revoke
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            jti = payload.get("jti")
            if jti:
                self._blacklist.add(jti)
                logger.info(f"Token revoked: {jti}")
        except Exception as e:
            logger.error(f"Error revoking token: {e}")


class JWTAuthenticator:
    """
    JWT Authentication Handler for FastAPI
    """

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.bearer_scheme = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request) -> TokenPayload:
        """
        Authenticate request using JWT bearer token

        Args:
            request: FastAPI request object

        Returns:
            Validated token payload

        Raises:
            HTTPException: If authentication fails
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Parse bearer token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify token
        payload = self.token_manager.verify_token(token)

        # Attach user info to request state
        request.state.user_id = payload.sub
        request.state.roles = payload.roles
        request.state.permissions = payload.permissions

        return payload


def require_roles(*required_roles: str):
    """
    Decorator to require specific roles for endpoint access

    Args:
        required_roles: Required role names

    Example:
        @require_roles("admin", "analyst")
        async def admin_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            user_roles = getattr(request.state, 'roles', [])
            if not any(role in user_roles for role in required_roles):
                logger.warning(
                    f"Access denied: User roles {user_roles} do not match "
                    f"required roles {required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*required_permissions: str):
    """
    Decorator to require specific permissions for endpoint access

    Args:
        required_permissions: Required permission names

    Example:
        @require_permissions("filings.read", "predictions.write")
        async def protected_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            user_permissions = getattr(request.state, 'permissions', [])
            if not all(perm in user_permissions for perm in required_permissions):
                logger.warning(
                    f"Access denied: User permissions {user_permissions} do not match "
                    f"required permissions {required_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

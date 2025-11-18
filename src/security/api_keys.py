"""
API Key Management System
Handles generation, validation, rotation, and revocation of API keys
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class APIKeyStatus(str, Enum):
    """API Key Status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKeyMetadata(BaseModel):
    """API Key Metadata"""
    key_id: str
    name: str
    description: Optional[str] = None
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rate_limit: Optional[int] = None  # Requests per minute
    allowed_ips: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class APIKeyManager:
    """
    Manages API key lifecycle including generation, validation, and rotation
    """

    def __init__(
        self,
        secret_key: str,
        key_prefix: str = "sk_",
        default_expiry_days: int = 90
    ):
        """
        Initialize APIKeyManager

        Args:
            secret_key: Secret key for HMAC signing
            key_prefix: Prefix for generated keys
            default_expiry_days: Default expiration period in days
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.secret_key = secret_key.encode()
        self.key_prefix = key_prefix
        self.default_expiry_days = default_expiry_days

        # In-memory storage (use database in production)
        self._keys: Dict[str, APIKeyMetadata] = {}
        self._key_hashes: Dict[str, str] = {}  # hash -> key_id mapping

        logger.info("APIKeyManager initialized")

    def generate_key(
        self,
        name: str,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        allowed_ips: List[str] = None,
        scopes: List[str] = None
    ) -> tuple[str, APIKeyMetadata]:
        """
        Generate new API key

        Args:
            name: Human-readable key name
            description: Optional description
            expires_in_days: Expiration period (default: 90 days)
            rate_limit: Rate limit in requests per minute
            allowed_ips: Whitelist of allowed IP addresses
            scopes: List of permission scopes

        Returns:
            Tuple of (api_key, metadata)
        """
        # Generate random key
        random_bytes = secrets.token_bytes(32)
        key_id = secrets.token_urlsafe(16)

        # Create API key with prefix
        api_key = f"{self.key_prefix}{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = self._hash_key(api_key)

        # Create metadata
        now = datetime.utcnow()
        expires_at = None
        if expires_in_days or self.default_expiry_days:
            days = expires_in_days or self.default_expiry_days
            expires_at = now + timedelta(days=days)

        metadata = APIKeyMetadata(
            key_id=key_id,
            name=name,
            description=description,
            created_at=now,
            expires_at=expires_at,
            rate_limit=rate_limit,
            allowed_ips=allowed_ips or [],
            scopes=scopes or []
        )

        # Store metadata and hash mapping
        self._keys[key_id] = metadata
        self._key_hashes[key_hash] = key_id

        logger.info(f"Generated API key: {key_id} ({name})")

        return api_key, metadata

    def validate_key(
        self,
        api_key: str,
        required_scopes: List[str] = None,
        client_ip: Optional[str] = None
    ) -> Optional[APIKeyMetadata]:
        """
        Validate API key and check permissions

        Args:
            api_key: API key to validate
            required_scopes: Required permission scopes
            client_ip: Client IP address for whitelist check

        Returns:
            API key metadata if valid, None otherwise
        """
        # Hash the provided key
        key_hash = self._hash_key(api_key)

        # Look up key ID
        key_id = self._key_hashes.get(key_hash)
        if not key_id:
            logger.warning("Invalid API key used")
            return None

        # Get metadata
        metadata = self._keys.get(key_id)
        if not metadata:
            logger.warning(f"Metadata not found for key: {key_id}")
            return None

        # Check status
        if metadata.status != APIKeyStatus.ACTIVE:
            logger.warning(f"Inactive API key used: {key_id} (status: {metadata.status})")
            return None

        # Check expiration
        if metadata.expires_at and datetime.utcnow() > metadata.expires_at:
            logger.warning(f"Expired API key used: {key_id}")
            metadata.status = APIKeyStatus.EXPIRED
            return None

        # Check IP whitelist
        if metadata.allowed_ips and client_ip:
            if client_ip not in metadata.allowed_ips:
                logger.warning(
                    f"IP {client_ip} not whitelisted for key {key_id}. "
                    f"Allowed: {metadata.allowed_ips}"
                )
                return None

        # Check scopes
        if required_scopes:
            if not all(scope in metadata.scopes for scope in required_scopes):
                logger.warning(
                    f"Insufficient scopes for key {key_id}. "
                    f"Required: {required_scopes}, Available: {metadata.scopes}"
                )
                return None

        # Update usage stats
        metadata.last_used_at = datetime.utcnow()
        metadata.usage_count += 1

        logger.debug(f"API key validated: {key_id}")
        return metadata

    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke API key

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked, False if not found
        """
        metadata = self._keys.get(key_id)
        if not metadata:
            logger.warning(f"Key not found for revocation: {key_id}")
            return False

        metadata.status = APIKeyStatus.REVOKED
        logger.info(f"API key revoked: {key_id}")
        return True

    def rotate_key(
        self,
        old_key_id: str,
        grace_period_days: int = 7
    ) -> tuple[str, APIKeyMetadata]:
        """
        Rotate API key (create new key and schedule old key for revocation)

        Args:
            old_key_id: Key ID to rotate
            grace_period_days: Days before old key is revoked

        Returns:
            Tuple of (new_api_key, new_metadata)
        """
        old_metadata = self._keys.get(old_key_id)
        if not old_metadata:
            raise ValueError(f"Key not found: {old_key_id}")

        # Create new key with same properties
        new_key, new_metadata = self.generate_key(
            name=f"{old_metadata.name} (rotated)",
            description=old_metadata.description,
            rate_limit=old_metadata.rate_limit,
            allowed_ips=old_metadata.allowed_ips,
            scopes=old_metadata.scopes
        )

        # Schedule old key expiration
        old_metadata.expires_at = datetime.utcnow() + timedelta(days=grace_period_days)

        logger.info(
            f"API key rotated: {old_key_id} -> {new_metadata.key_id}. "
            f"Grace period: {grace_period_days} days"
        )

        return new_key, new_metadata

    def list_keys(
        self,
        status_filter: Optional[APIKeyStatus] = None
    ) -> List[APIKeyMetadata]:
        """
        List all API keys

        Args:
            status_filter: Optional status filter

        Returns:
            List of API key metadata
        """
        keys = list(self._keys.values())
        if status_filter:
            keys = [k for k in keys if k.status == status_filter]
        return keys

    def get_key_info(self, key_id: str) -> Optional[APIKeyMetadata]:
        """
        Get API key metadata

        Args:
            key_id: Key ID

        Returns:
            API key metadata if found
        """
        return self._keys.get(key_id)

    def _hash_key(self, api_key: str) -> str:
        """
        Generate HMAC hash of API key

        Args:
            api_key: API key to hash

        Returns:
            Hex digest of HMAC-SHA256
        """
        return hmac.new(
            self.secret_key,
            api_key.encode(),
            hashlib.sha256
        ).hexdigest()

    def export_keys(self) -> str:
        """
        Export all keys as JSON (for backup/migration)

        Returns:
            JSON string of all keys
        """
        export_data = {
            key_id: {
                "name": meta.name,
                "description": meta.description,
                "status": meta.status.value,
                "created_at": meta.created_at.isoformat(),
                "expires_at": meta.expires_at.isoformat() if meta.expires_at else None,
                "rate_limit": meta.rate_limit,
                "allowed_ips": meta.allowed_ips,
                "scopes": meta.scopes,
                "usage_count": meta.usage_count
            }
            for key_id, meta in self._keys.items()
        }
        return json.dumps(export_data, indent=2)

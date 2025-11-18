"""
Secrets Management Integration
HashiCorp Vault and AWS Secrets Manager support
"""

import os
from typing import Optional, Dict, Any
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretProvider(str, Enum):
    """Secret provider types"""
    ENVIRONMENT = "environment"
    VAULT = "vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    FILE = "file"


class SecretStore(ABC):
    """
    Abstract base class for secret storage backends
    """

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value by key"""
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret value"""
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete secret"""
        pass

    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List all secret keys"""
        pass


class EnvironmentSecretStore(SecretStore):
    """
    Environment variable-based secret storage
    """

    def __init__(self, prefix: str = "SECRET_"):
        """
        Initialize environment secret store

        Args:
            prefix: Prefix for secret environment variables
        """
        self.prefix = prefix
        logger.info(f"EnvironmentSecretStore initialized with prefix: {prefix}")

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variable"""
        env_key = f"{self.prefix}{key.upper()}"
        value = os.environ.get(env_key)
        if value:
            logger.debug(f"Retrieved secret: {key}")
        return value

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in environment (runtime only)"""
        env_key = f"{self.prefix}{key.upper()}"
        os.environ[env_key] = value
        logger.info(f"Set secret: {key}")
        return True

    def delete_secret(self, key: str) -> bool:
        """Delete secret from environment"""
        env_key = f"{self.prefix}{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            logger.info(f"Deleted secret: {key}")
            return True
        return False

    def list_secrets(self) -> list[str]:
        """List all secret keys"""
        return [
            key.replace(self.prefix, "").lower()
            for key in os.environ.keys()
            if key.startswith(self.prefix)
        ]


class VaultSecretStore(SecretStore):
    """
    HashiCorp Vault secret storage
    """

    def __init__(
        self,
        vault_addr: str,
        vault_token: Optional[str] = None,
        mount_point: str = "secret",
        namespace: Optional[str] = None
    ):
        """
        Initialize Vault secret store

        Args:
            vault_addr: Vault server address
            vault_token: Vault token (from env if not provided)
            mount_point: KV mount point
            namespace: Vault namespace
        """
        self.vault_addr = vault_addr
        self.vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self.mount_point = mount_point
        self.namespace = namespace

        if not self.vault_token:
            raise ValueError("Vault token not provided")

        # Import hvac library
        try:
            import hvac
            self.client = hvac.Client(
                url=self.vault_addr,
                token=self.vault_token,
                namespace=self.namespace
            )

            if not self.client.is_authenticated():
                raise ValueError("Vault authentication failed")

            logger.info(f"VaultSecretStore initialized: {vault_addr}")
        except ImportError:
            raise ImportError("hvac library required for Vault integration")

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=key,
                mount_point=self.mount_point
            )
            value = response['data']['data'].get('value')
            if value:
                logger.debug(f"Retrieved secret from Vault: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=key,
                secret={'value': value},
                mount_point=self.mount_point
            )
            logger.info(f"Set secret in Vault: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=key,
                mount_point=self.mount_point
            )
            logger.info(f"Deleted secret from Vault: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False

    def list_secrets(self) -> list[str]:
        """List all secret keys in Vault"""
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path='',
                mount_point=self.mount_point
            )
            return response['data']['keys']
        except Exception as e:
            logger.error(f"Failed to list secrets from Vault: {e}")
            return []


class AWSSecretsManagerStore(SecretStore):
    """
    AWS Secrets Manager secret storage
    """

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize AWS Secrets Manager store

        Args:
            region_name: AWS region
        """
        self.region_name = region_name

        try:
            import boto3
            self.client = boto3.client(
                'secretsmanager',
                region_name=region_name
            )
            logger.info(f"AWSSecretsManagerStore initialized: {region_name}")
        except ImportError:
            raise ImportError("boto3 library required for AWS Secrets Manager")

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=key)
            value = response.get('SecretString')
            if value:
                logger.debug(f"Retrieved secret from AWS: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve secret from AWS: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager"""
        try:
            # Try to update first
            try:
                self.client.update_secret(
                    SecretId=key,
                    SecretString=value
                )
            except self.client.exceptions.ResourceNotFoundException:
                # Create if doesn't exist
                self.client.create_secret(
                    Name=key,
                    SecretString=value
                )
            logger.info(f"Set secret in AWS: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in AWS: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            self.client.delete_secret(
                SecretId=key,
                ForceDeleteWithoutRecovery=True
            )
            logger.info(f"Deleted secret from AWS: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from AWS: {e}")
            return False

    def list_secrets(self) -> list[str]:
        """List all secret keys in AWS Secrets Manager"""
        try:
            response = self.client.list_secrets()
            return [secret['Name'] for secret in response['SecretList']]
        except Exception as e:
            logger.error(f"Failed to list secrets from AWS: {e}")
            return []


class SecretsManager:
    """
    Unified secrets manager with multiple backend support
    """

    def __init__(
        self,
        provider: SecretProvider = SecretProvider.ENVIRONMENT,
        **provider_config
    ):
        """
        Initialize secrets manager

        Args:
            provider: Secret provider type
            **provider_config: Provider-specific configuration
        """
        self.provider = provider

        # Initialize appropriate backend
        if provider == SecretProvider.ENVIRONMENT:
            self.store = EnvironmentSecretStore(
                prefix=provider_config.get('prefix', 'SECRET_')
            )
        elif provider == SecretProvider.VAULT:
            self.store = VaultSecretStore(**provider_config)
        elif provider == SecretProvider.AWS_SECRETS_MANAGER:
            self.store = AWSSecretsManagerStore(**provider_config)
        else:
            raise ValueError(f"Unsupported secret provider: {provider}")

        logger.info(f"SecretsManager initialized with {provider} provider")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value

        Args:
            key: Secret key
            default: Default value if not found

        Returns:
            Secret value or default
        """
        value = self.store.get_secret(key)
        return value if value is not None else default

    def get_required(self, key: str) -> str:
        """
        Get required secret (raises error if not found)

        Args:
            key: Secret key

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found
        """
        value = self.store.get_secret(key)
        if value is None:
            raise ValueError(f"Required secret not found: {key}")
        return value

    def set(self, key: str, value: str) -> bool:
        """
        Set secret value

        Args:
            key: Secret key
            value: Secret value

        Returns:
            True if successful
        """
        return self.store.set_secret(key, value)

    def delete(self, key: str) -> bool:
        """
        Delete secret

        Args:
            key: Secret key

        Returns:
            True if successful
        """
        return self.store.delete_secret(key)

    def list_all(self) -> list[str]:
        """
        List all secret keys

        Returns:
            List of secret keys
        """
        return self.store.list_secrets()


# Default secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def init_secrets(
    provider: SecretProvider = SecretProvider.ENVIRONMENT,
    **provider_config
):
    """
    Initialize global secrets manager

    Args:
        provider: Secret provider type
        **provider_config: Provider-specific configuration
    """
    global _secrets_manager
    _secrets_manager = SecretsManager(provider, **provider_config)
    logger.info("Global secrets manager initialized")


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from global manager

    Args:
        key: Secret key
        default: Default value

    Returns:
        Secret value or default
    """
    if _secrets_manager is None:
        init_secrets()
    return _secrets_manager.get(key, default)


def get_required_secret(key: str) -> str:
    """
    Get required secret from global manager

    Args:
        key: Secret key

    Returns:
        Secret value

    Raises:
        ValueError: If secret not found
    """
    if _secrets_manager is None:
        init_secrets()
    return _secrets_manager.get_required(key)

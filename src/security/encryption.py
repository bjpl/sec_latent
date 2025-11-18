"""
Encryption Utilities
AES-256 encryption for data at rest and sensitive information
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    AES-256-GCM encryption service for data at rest
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize EncryptionService

        Args:
            master_key: Base64-encoded 256-bit master key (generated if not provided)
        """
        if master_key:
            self.master_key = base64.b64decode(master_key)
        else:
            # Generate random 256-bit key
            self.master_key = os.urandom(32)
            logger.info("Generated new master encryption key")

        if len(self.master_key) != 32:
            raise ValueError("Master key must be 256 bits (32 bytes)")

        self.backend = default_backend()
        logger.info("EncryptionService initialized with AES-256-GCM")

    def encrypt(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None
    ) -> str:
        """
        Encrypt data using AES-256-GCM

        Args:
            plaintext: Data to encrypt (string or bytes)
            associated_data: Optional authenticated associated data (AAD)

        Returns:
            Base64-encoded ciphertext with format: nonce:tag:ciphertext
        """
        # Convert string to bytes if necessary
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        # Generate random nonce (96 bits for GCM)
        nonce = os.urandom(12)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.GCM(nonce),
            backend=self.backend
        )
        encryptor = cipher.encryptor()

        # Add associated data if provided
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)

        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Get authentication tag
        tag = encryptor.tag

        # Combine nonce:tag:ciphertext and encode
        combined = nonce + tag + ciphertext
        encoded = base64.b64encode(combined).decode('utf-8')

        logger.debug(f"Encrypted {len(plaintext)} bytes -> {len(encoded)} chars")
        return encoded

    def decrypt(
        self,
        ciphertext: str,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Decrypt data using AES-256-GCM

        Args:
            ciphertext: Base64-encoded ciphertext
            associated_data: Optional authenticated associated data (AAD)

        Returns:
            Decrypted plaintext as bytes

        Raises:
            ValueError: If decryption fails (wrong key or corrupted data)
        """
        try:
            # Decode from base64
            combined = base64.b64decode(ciphertext)

            # Extract nonce (12 bytes), tag (16 bytes), and ciphertext
            nonce = combined[:12]
            tag = combined[12:28]
            encrypted_data = combined[28:]

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(nonce, tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()

            # Add associated data if provided
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)

            # Decrypt
            plaintext = decryptor.update(encrypted_data) + decryptor.finalize()

            logger.debug(f"Decrypted {len(ciphertext)} chars -> {len(plaintext)} bytes")
            return plaintext

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or corrupted data")

    def decrypt_to_string(
        self,
        ciphertext: str,
        associated_data: Optional[bytes] = None
    ) -> str:
        """
        Decrypt data and return as UTF-8 string

        Args:
            ciphertext: Base64-encoded ciphertext
            associated_data: Optional authenticated associated data (AAD)

        Returns:
            Decrypted plaintext as string
        """
        plaintext_bytes = self.decrypt(ciphertext, associated_data)
        return plaintext_bytes.decode('utf-8')

    def derive_key(
        self,
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = 100000
    ) -> tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)
            iterations: Number of iterations (default: 100,000)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=self.backend
        )

        key = kdf.derive(password.encode('utf-8'))
        logger.debug("Derived encryption key from password")
        return key, salt

    def encrypt_field(
        self,
        data: dict,
        field_name: str,
        in_place: bool = False
    ) -> dict:
        """
        Encrypt specific field in dictionary

        Args:
            data: Dictionary containing field to encrypt
            field_name: Name of field to encrypt
            in_place: Modify dictionary in place (default: False)

        Returns:
            Dictionary with encrypted field
        """
        if not in_place:
            data = data.copy()

        if field_name in data:
            value = data[field_name]
            if value is not None:
                encrypted = self.encrypt(str(value))
                data[field_name] = encrypted
                logger.debug(f"Encrypted field: {field_name}")

        return data

    def decrypt_field(
        self,
        data: dict,
        field_name: str,
        in_place: bool = False
    ) -> dict:
        """
        Decrypt specific field in dictionary

        Args:
            data: Dictionary containing field to decrypt
            field_name: Name of field to decrypt
            in_place: Modify dictionary in place (default: False)

        Returns:
            Dictionary with decrypted field
        """
        if not in_place:
            data = data.copy()

        if field_name in data:
            encrypted_value = data[field_name]
            if encrypted_value is not None:
                try:
                    decrypted = self.decrypt_to_string(encrypted_value)
                    data[field_name] = decrypted
                    logger.debug(f"Decrypted field: {field_name}")
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field_name}: {e}")

        return data

    def get_master_key_b64(self) -> str:
        """
        Get base64-encoded master key (for backup/configuration)

        Returns:
            Base64-encoded master key
        """
        return base64.b64encode(self.master_key).decode('utf-8')

    @staticmethod
    def generate_key() -> str:
        """
        Generate new random 256-bit key

        Returns:
            Base64-encoded key
        """
        key = os.urandom(32)
        return base64.b64encode(key).decode('utf-8')


class FieldEncryptor:
    """
    Utility class for encrypting specific fields in data structures
    """

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service

    def encrypt_sensitive_fields(
        self,
        data: dict,
        sensitive_fields: list[str]
    ) -> dict:
        """
        Encrypt multiple sensitive fields in dictionary

        Args:
            data: Dictionary to process
            sensitive_fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field in sensitive_fields:
            if field in result:
                result = self.encryption.encrypt_field(result, field)
        return result

    def decrypt_sensitive_fields(
        self,
        data: dict,
        sensitive_fields: list[str]
    ) -> dict:
        """
        Decrypt multiple sensitive fields in dictionary

        Args:
            data: Dictionary to process
            sensitive_fields: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field in sensitive_fields:
            if field in result:
                result = self.encryption.decrypt_field(result, field)
        return result

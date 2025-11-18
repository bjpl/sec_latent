# Security Implementation Documentation

## Overview
Comprehensive security implementation for SEC Latent Analysis API following industry best practices and OWASP guidelines.

## Components Implemented

### 1. JWT Authentication System
**Location**: `src/security/auth.py`

**Features**:
- JWT token generation with HS256 algorithm
- Access tokens (30 min expiry) and refresh tokens (7 day expiry)
- Token refresh mechanism
- Token revocation with blacklist
- Role and permission embedding in tokens
- Decorators for role-based access control

**Usage**:
```python
from src.security.auth import TokenManager, JWTAuthenticator, require_roles

# Initialize
token_manager = TokenManager(secret_key="your-secret", algorithm="HS256")
authenticator = JWTAuthenticator(token_manager)

# Generate tokens
access_token = token_manager.create_access_token(
    user_id="user123",
    roles=["analyst"],
    permissions=["filings.read", "predictions.read"]
)

# Protect endpoints
@require_roles("admin", "analyst")
async def protected_endpoint(request: Request):
    pass
```

### 2. API Key Management
**Location**: `src/security/api_keys.py`

**Features**:
- Secure API key generation with cryptographic randomness
- HMAC-SHA256 key hashing for storage
- Key expiration and rotation
- Rate limiting per key
- IP whitelisting
- Scope-based permissions
- Usage tracking

**Usage**:
```python
from src.security.api_keys import APIKeyManager

manager = APIKeyManager(secret_key="your-secret")

# Generate API key
api_key, metadata = manager.generate_key(
    name="Production API",
    expires_in_days=90,
    rate_limit=1000,
    scopes=["filings.read", "predictions.read"]
)

# Validate key
metadata = manager.validate_key(api_key, client_ip="192.168.1.1")
```

### 3. AES-256 Encryption
**Location**: `src/security/encryption.py`

**Features**:
- AES-256-GCM encryption for data at rest
- Authenticated encryption with additional data (AEAD)
- Key derivation from passwords using PBKDF2
- Field-level encryption utilities
- Master key management

**Usage**:
```python
from src.security.encryption import EncryptionService

service = EncryptionService(master_key="base64-encoded-key")

# Encrypt data
ciphertext = service.encrypt("sensitive data")

# Decrypt data
plaintext = service.decrypt_to_string(ciphertext)

# Encrypt specific fields
data = {"name": "John", "ssn": "123-45-6789"}
encrypted_data = service.encrypt_field(data, "ssn")
```

### 4. Role-Based Access Control (RBAC)
**Location**: `src/rbac/`

**Features**:
- Hierarchical role system with inheritance
- Permission-based authorization
- Predefined roles: guest, analyst, api_user, manager, admin
- Fine-grained permissions for all resources
- Role decorators for endpoint protection

**Roles**:
- **guest**: Read-only access
- **analyst**: Read/write access to data
- **api_user**: Programmatic API access
- **manager**: User management + analyst permissions
- **admin**: Full system access

**Usage**:
```python
from src.rbac import init_rbac, require_permission, Permission

# Initialize RBAC
init_rbac()

# Protect endpoint with permission
@require_permission(Permission.FILINGS_WRITE, resource_name="filings")
async def create_filing(request: Request):
    pass
```

### 5. Rate Limiting
**Location**: `src/middleware/rate_limit.py`

**Features**:
- Token bucket algorithm implementation
- Per-user/IP rate limiting
- Configurable limits per endpoint
- Burst capacity handling
- Automatic cleanup of old buckets
- Rate limit headers in responses

**Usage**:
```python
from src.middleware import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=120,
    custom_limits={
        "/api/v1/filings": 100,
        "/api/v1/predictions": 60
    }
)
```

### 6. Audit Logging
**Location**: `src/security/audit.py`

**Features**:
- Structured JSON logging
- Event types: authentication, authorization, data access, security events
- Comprehensive metadata capture
- File and console output
- Audit trail for compliance

**Usage**:
```python
from src.security.audit import AuditLogger

logger = AuditLogger(
    log_file="logs/audit.log",
    json_format=True
)

# Log authentication
logger.log_authentication(
    user_id="user123",
    success=True,
    ip_address="192.168.1.1"
)

# Log authorization
logger.log_authorization(
    user_id="user123",
    resource="filings",
    action="write",
    granted=True
)
```

### 7. Security Headers
**Location**: `src/middleware/security_headers.py`

**Features**:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
- Enhanced CORS with security checks

**Usage**:
```python
from src.middleware import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_max_age=31536000,
    frame_options="DENY",
    csp_directives={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"]
    }
)
```

### 8. Input Validation & Sanitization
**Location**: `src/utils/validation.py`

**Features**:
- SQL injection prevention
- XSS attack prevention
- Command injection prevention
- Filename sanitization (path traversal prevention)
- Email validation
- URL validation
- Integer/float range validation
- Recursive dictionary sanitization

**Usage**:
```python
from src.utils.validation import InputSanitizer, ValidationError

try:
    # Sanitize string
    clean_text = InputSanitizer.sanitize_string(
        user_input,
        max_length=1000
    )

    # Validate email
    email = InputSanitizer.sanitize_email("user@example.com")

    # Sanitize filename
    filename = InputSanitizer.sanitize_filename("report.pdf")

except ValidationError as e:
    print(f"Validation failed: {e}")
```

### 9. Secrets Management
**Location**: `src/utils/secrets.py`

**Features**:
- Multiple backend support (Environment, Vault, AWS Secrets Manager)
- Unified API for secret retrieval
- Automatic provider initialization
- Secret rotation support

**Supported Providers**:
- Environment variables
- HashiCorp Vault
- AWS Secrets Manager

**Usage**:
```python
from src.utils.secrets import init_secrets, get_secret, SecretProvider

# Initialize with Vault
init_secrets(
    provider=SecretProvider.VAULT,
    vault_addr="https://vault.example.com",
    vault_token="vault-token"
)

# Get secrets
db_password = get_secret("database_password")
api_key = get_secret("external_api_key")
```

## Security Configuration
**Location**: `config/security_config.py`

Centralized configuration with environment-based settings:
- JWT token expiration times
- Rate limit thresholds
- CORS origins
- Security header policies
- Audit logging settings
- Secrets provider configuration

## Integration Example

```python
from fastapi import FastAPI
from src.security.auth import TokenManager, JWTAuthenticator
from src.security.api_keys import APIKeyManager
from src.security.audit import AuditLogger
from src.middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware
)
from src.rbac import init_rbac
from config.security_config import get_security_config

app = FastAPI()
config = get_security_config()

# Initialize security components
token_manager = TokenManager(
    secret_key=config.jwt_secret_key,
    algorithm=config.jwt_algorithm
)
api_key_manager = APIKeyManager(secret_key=config.api_key_secret)
audit_logger = AuditLogger(log_file=config.audit_log_file)

# Initialize RBAC
init_rbac(audit_logger=audit_logger)

# Add middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware, ...)
app.add_middleware(RateLimitMiddleware, ...)
app.add_middleware(AuthenticationMiddleware, ...)
```

## Security Best Practices

1. **Environment Variables**: Store all secrets in environment variables or secret managers
2. **TLS/HTTPS**: Always use TLS 1.3 in production
3. **Key Rotation**: Rotate JWT keys and API keys regularly
4. **Audit Logging**: Review audit logs regularly for suspicious activity
5. **Rate Limiting**: Tune rate limits based on usage patterns
6. **Input Validation**: Validate all user input before processing
7. **Least Privilege**: Assign minimum required permissions
8. **Monitoring**: Set up alerts for security events

## Testing Requirements

All security components include comprehensive tests:
- Unit tests for authentication and authorization
- Integration tests for middleware
- Security tests for injection vulnerabilities
- Performance tests for rate limiting

## Compliance

This implementation follows:
- OWASP Top 10 security guidelines
- NIST cybersecurity framework
- PCI DSS requirements (where applicable)
- GDPR data protection principles

## Dependencies

Required Python packages:
- PyJWT >= 2.8.0 (JWT tokens)
- cryptography >= 41.0.0 (Encryption)
- pydantic >= 2.0.0 (Configuration)
- hvac >= 1.2.1 (Vault - optional)
- boto3 >= 1.28.0 (AWS - optional)

## Production Checklist

- [ ] Change default JWT secret key
- [ ] Change default API key secret
- [ ] Generate and store encryption master key
- [ ] Configure TLS certificates
- [ ] Set up secrets manager (Vault or AWS)
- [ ] Configure production CORS origins
- [ ] Enable audit logging
- [ ] Set up log aggregation (e.g., ELK stack)
- [ ] Configure IP whitelisting if needed
- [ ] Set appropriate rate limits
- [ ] Enable security headers
- [ ] Configure automated key rotation
- [ ] Set up security monitoring and alerts

## Maintenance

- Review audit logs weekly
- Rotate JWT keys monthly
- Review and update role permissions quarterly
- Update dependencies for security patches
- Conduct security audits annually

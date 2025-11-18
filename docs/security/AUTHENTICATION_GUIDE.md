# Authentication & Authorization Guide

## Overview

This guide provides comprehensive documentation for authentication and authorization in the SEC Latent Signal Analysis Platform, including JWT implementation, API key management, OAuth2 flows, and RBAC configuration.

## Table of Contents

- [Authentication Methods](#authentication-methods)
- [JWT Authentication](#jwt-authentication)
- [API Key Authentication](#api-key-authentication)
- [OAuth2 Integration](#oauth2-integration)
- [Role-Based Access Control](#role-based-access-control)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Authentication Methods

The platform supports multiple authentication methods:

| Method | Use Case | Token Lifetime | Security Level |
|--------|----------|----------------|----------------|
| **JWT** | Web applications, SPAs | 15 min (access) / 7 days (refresh) | High |
| **API Keys** | Programmatic access, integrations | 90 days (rotatable) | High |
| **OAuth2** | Third-party integrations | Varies by provider | High |
| **Service Accounts** | Internal services | N/A (long-lived) | Critical |

## JWT Authentication

### Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-2025-01"
  },
  "payload": {
    "sub": "user_uuid",
    "email": "user@example.com",
    "roles": ["analyst", "trader"],
    "permissions": ["filings:read", "signals:extract"],
    "org_id": "org_uuid",
    "tier": "enterprise",
    "iat": 1729284000,
    "exp": 1729287600,
    "jti": "token_uuid"
  },
  "signature": "..."
}
```

### Obtaining Access Token

**Request:**
```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Python Example:**
```python
import requests

# Obtain token
response = requests.post(
    "https://api.sec-analysis.com/v1/auth/token",
    json={"email": "user@example.com", "password": "password"}
)
token_data = response.json()
access_token = token_data["access_token"]

# Use token
headers = {"Authorization": f"Bearer {access_token}"}
filings = requests.get(
    "https://api.sec-analysis.com/v1/filings",
    headers=headers
)
```

### Token Refresh

When access token expires, use refresh token to obtain new access token without re-authentication.

**Request:**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // New refresh token
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Important**: Refresh tokens are **one-time use** and automatically rotate on each refresh.

### Token Revocation

Immediately invalidate access and refresh tokens.

**Request:**
```http
POST /api/v1/auth/revoke
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type_hint": "access_token"  // or "refresh_token"
}
```

**Use Cases:**
- User logout
- Security incident
- Suspicious activity detected
- Password change
- Role change

## API Key Authentication

### Creating API Key

**Request:**
```http
POST /api/v1/auth/api-keys
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "name": "Production Integration",
  "scopes": ["filings:read", "signals:extract"],
  "expires_in_days": 90
}
```

**Response:**
```json
{
  "api_key": "slat_v1_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  // Full key (shown once)
  "key_id": "key_uuid",
  "key_prefix": "slat_v1_a1b2c3d4...",
  "name": "Production Integration",
  "scopes": ["filings:read", "signals:extract"],
  "created_at": "2025-10-18T10:00:00Z",
  "expires_at": "2026-01-16T10:00:00Z",
  "rate_limit": 1000  // requests per hour
}
```

**IMPORTANT**: Store the full API key securely. It will not be shown again.

### Using API Key

**HTTP Header (Recommended):**
```http
GET /api/v1/filings
Authorization: Bearer slat_v1_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Query Parameter (Not Recommended):**
```http
GET /api/v1/filings?api_key=slat_v1_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Python Example:**
```python
import requests

API_KEY = "slat_v1_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.get(
    "https://api.sec-analysis.com/v1/filings",
    headers=headers
)
```

### API Key Rotation

Rotate API keys before expiration to maintain uninterrupted service.

**Request:**
```http
POST /api/v1/auth/api-keys/{key_id}/rotate
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "new_api_key": "slat_v1_new_key_here",
  "old_key_id": "old_key_uuid",
  "new_key_id": "new_key_uuid",
  "grace_period_ends": "2025-10-25T10:00:00Z"  // Old key valid for 7 days
}
```

**Rotation Process:**
1. Generate new API key
2. Update application with new key
3. Verify new key works
4. Old key remains valid for 7-day grace period
5. After grace period, old key is automatically revoked

### Listing API Keys

**Request:**
```http
GET /api/v1/auth/api-keys
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "count": 3,
  "api_keys": [
    {
      "key_id": "key_uuid_1",
      "key_prefix": "slat_v1_a1b2c3d4...",
      "name": "Production Integration",
      "scopes": ["filings:read", "signals:extract"],
      "created_at": "2025-10-18T10:00:00Z",
      "last_used_at": "2025-10-18T14:30:00Z",
      "expires_at": "2026-01-16T10:00:00Z",
      "is_active": true
    }
  ]
}
```

### Revoking API Key

**Request:**
```http
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "key_id": "key_uuid",
  "status": "revoked",
  "revoked_at": "2025-10-18T15:00:00Z"
}
```

## OAuth2 Integration

### Supported Providers

- Google OAuth2
- Microsoft Azure AD
- GitHub
- Okta
- Generic OIDC

### OAuth2 Flow

```
User → Click "Login with Google"
  ↓
Application → Redirect to Google
  ↓
User → Authorize application (Google)
  ↓
Google → Redirect back with authorization code
  ↓
Application → Exchange code for access token
  ↓
Application → Fetch user profile
  ↓
Application → Create/update user account
  ↓
Application → Generate JWT access token
  ↓
User → Authenticated
```

### Configuration

**Google OAuth2:**
```python
# config/oauth.py

OAUTH2_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scopes": ["openid", "email", "profile"]
    }
}
```

### Initiate OAuth2 Flow

**Request:**
```http
GET /api/v1/auth/oauth2/google/authorize
```

**Response (Redirect):**
```
Location: https://accounts.google.com/o/oauth2/v2/auth?
  client_id=...&
  redirect_uri=...&
  scope=openid email profile&
  response_type=code&
  state=...
```

### OAuth2 Callback

**Request (from Google):**
```http
GET /api/v1/auth/oauth2/google/callback?code=...&state=...
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "user_uuid",
    "email": "user@gmail.com",
    "name": "John Doe",
    "picture": "https://..."
  }
}
```

## Role-Based Access Control

### Permission Model

Permissions follow the pattern: `<resource>:<action>:<scope>`

**Examples:**
- `filings:read:own` - Read own filings
- `filings:read:organization` - Read organization filings
- `filings:read:all` - Read all filings
- `signals:extract:own` - Extract signals from own filings
- `users:manage:organization` - Manage organization users
- `api_keys:create:own` - Create own API keys

### Built-in Roles

| Role | Permissions | Description |
|------|-------------|-------------|
| **Admin** | `*:*:all` | Full system access |
| **Analyst** | `filings:read:organization`<br>`signals:extract:organization`<br>`signals:read:organization` | Analyze filings and extract signals |
| **Viewer** | `filings:read:organization`<br>`signals:read:organization` | Read-only access |
| **API Developer** | `filings:read:organization`<br>`signals:extract:organization`<br>`api_keys:create:own` | Programmatic access |

### Assigning Roles

**Request:**
```http
POST /api/v1/users/{user_id}/roles
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "role_id": "analyst",
  "expires_at": "2026-10-18T00:00:00Z"  // Optional
}
```

**Response:**
```json
{
  "user_id": "user_uuid",
  "role_id": "analyst",
  "granted_at": "2025-10-18T10:00:00Z",
  "granted_by": "admin_uuid",
  "expires_at": "2026-10-18T00:00:00Z"
}
```

### Custom Roles

**Request:**
```http
POST /api/v1/roles
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "name": "Compliance Officer",
  "description": "Access to compliance reports and audit logs",
  "permissions": [
    "filings:read:organization",
    "signals:read:organization",
    "audit_logs:read:organization",
    "compliance_reports:read:organization"
  ]
}
```

### Checking Permissions

**In API Endpoint:**
```python
from fastapi import Depends, HTTPException, status
from src.api.dependencies import require_permission

@app.get("/api/v1/filings")
async def list_filings(
    user=Depends(require_permission("filings:read:organization"))
):
    """List filings (requires permission)."""
    pass
```

**Programmatically:**
```python
from src.auth.rbac import check_permission

has_access = check_permission(
    user=current_user,
    permission="filings:read:organization"
)

if not has_access:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

## Security Best Practices

### Token Security

1. **Never expose tokens in URLs**
   - ❌ `https://api.example.com/filings?token=...`
   - ✅ `Authorization: Bearer ...` header

2. **Store tokens securely**
   - Web: HttpOnly cookies or memory (not localStorage)
   - Mobile: Secure storage (Keychain/Keystore)
   - Desktop: Encrypted credential storage

3. **Use short-lived access tokens**
   - Access token: 15 minutes
   - Refresh token: 7 days (one-time use)
   - Rotate refresh tokens on each use

4. **Implement token binding**
   - Optional: Bind tokens to IP address
   - Trade-off: Security vs. usability (mobile users)

### API Key Security

1. **Rotate keys regularly**
   - Recommended: Every 90 days
   - Automated rotation with grace period

2. **Use scoped keys**
   - Grant minimum required permissions
   - Create separate keys for different integrations

3. **Monitor key usage**
   - Track last_used_at timestamp
   - Alert on unusual activity
   - Automatic revocation on suspicious patterns

4. **Secure storage**
   - Environment variables (production)
   - Secret management systems (Vault, AWS Secrets Manager)
   - Never commit to version control

### Rate Limiting

**Per-User Limits:**
- Free tier: 100 requests/hour
- Basic tier: 1,000 requests/hour
- Pro tier: 10,000 requests/hour
- Enterprise tier: Custom limits

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 850
X-RateLimit-Reset: 1707217260
Retry-After: 60  (if rate limit exceeded)
```

### Multi-Factor Authentication

**Enable MFA:**
```http
POST /api/v1/auth/mfa/enable
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "method": "totp"  // or "sms", "email"
}
```

**Response:**
```json
{
  "method": "totp",
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "backup_codes": ["12345678", "87654321", ...]
}
```

**Login with MFA:**
```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password",
  "mfa_code": "123456"
}
```

## Troubleshooting

### Token Expired

**Error:**
```json
{
  "error": "token_expired",
  "message": "Access token has expired",
  "expired_at": "2025-10-18T10:15:00Z"
}
```

**Solution:** Use refresh token to obtain new access token.

### Invalid Token

**Error:**
```json
{
  "error": "invalid_token",
  "message": "Token signature verification failed"
}
```

**Possible Causes:**
- Token tampered with
- Wrong signing key
- Token from different environment

### Insufficient Permissions

**Error:**
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation",
  "required": "filings:write:organization",
  "granted": ["filings:read:organization"]
}
```

**Solution:** Request role/permission update from administrator.

### Rate Limit Exceeded

**Error:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60,
  "limit": 1000,
  "remaining": 0,
  "reset": 1707217260
}
```

**Solution:** Wait until reset time or upgrade tier.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Security Team
**Review Cycle**: Quarterly

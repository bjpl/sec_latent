# Comprehensive Security Architecture
**SEC Latent Signal Analysis Platform**

**Version**: 1.0
**Date**: 2025-10-18
**Researcher**: Security Research Agent
**Status**: ARCHITECTURAL RECOMMENDATIONS

---

## Executive Summary

This document provides comprehensive security architecture recommendations for the SEC Latent Signal Analysis Platform based on extensive research into industry best practices for JWT authentication, RBAC, API key management, encryption standards, anomaly detection, DDoS protection, and financial regulatory compliance (SOC 2, FINRA, SEC, GDPR/CCPA).

### Risk Assessment
- **Current State**: Pre-production development phase
- **Target State**: Production-ready enterprise financial analysis platform
- **Data Sensitivity**: HIGH (market-sensitive SEC filing analysis)
- **Regulatory Scope**: SEC, FINRA, GDPR/CCPA, SOC 2

---

## 1. Authentication Architecture

### 1.1 JWT (JSON Web Token) Implementation

#### Token Structure
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
    "permissions": ["read:filings", "read:signals"],
    "org_id": "org_uuid",
    "tier": "enterprise",
    "iat": 1729284000,
    "exp": 1729287600,
    "jti": "token_uuid"
  },
  "signature": "..."
}
```

#### Best Practices Implementation

**Token Security**:
- Use **RS256** (RSA + SHA-256) algorithm for production
- Rotate signing keys quarterly minimum
- Store private keys in HashiCorp Vault or AWS Secrets Manager
- Implement key versioning with `kid` header
- Never use HS256 in production (shared secret vulnerability)

**Token Lifecycle**:
- **Access Token**: 15-minute expiration
- **Refresh Token**: 7-day expiration, one-time use
- **Sliding Expiration**: Extend on activity
- **Revocation**: Maintain blacklist with Redis

**Refresh Token Strategy**:
```python
class TokenManager:
    def __init__(self, redis_client, jwt_secret):
        self.redis = redis_client
        self.jwt_secret = jwt_secret

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Rotate refresh token (one-time use)"""
        # Validate refresh token
        payload = self.validate_token(refresh_token)

        # Check if already used (Redis)
        token_id = payload.get("jti")
        if await self.redis.exists(f"used_token:{token_id}"):
            raise SecurityError("Refresh token already used")

        # Mark as used
        await self.redis.setex(
            f"used_token:{token_id}",
            86400 * 7,  # 7 days
            "1"
        )

        # Generate new token pair
        new_access = self.generate_access_token(payload["sub"])
        new_refresh = self.generate_refresh_token(payload["sub"])

        return new_access, new_refresh
```

**Token Storage (Client Side)**:
- **Access Token**: Memory only (no localStorage)
- **Refresh Token**: HttpOnly, Secure, SameSite=Strict cookie
- **CSRF Protection**: Custom header validation

#### Security Considerations

**Token Leakage Prevention**:
1. No tokens in URLs or query parameters
2. No tokens in client-side storage (localStorage/sessionStorage)
3. Short-lived access tokens
4. Rotating refresh tokens
5. Token binding to IP address (optional, strict)

**Token Revocation**:
```python
class TokenRevocation:
    async def revoke_token(self, token: str, reason: str):
        """Immediate token revocation"""
        payload = jwt.decode(token, verify=False)
        token_id = payload.get("jti")

        # Add to blacklist
        expiration = payload.get("exp") - int(time.time())
        await self.redis.setex(
            f"blacklist:{token_id}",
            max(expiration, 0),
            json.dumps({
                "reason": reason,
                "revoked_at": datetime.utcnow().isoformat()
            })
        )

        # Audit log
        await self.audit_log("token_revoked", {
            "token_id": token_id,
            "reason": reason,
            "user_id": payload.get("sub")
        })
```

---

## 2. Role-Based Access Control (RBAC)

### 2.1 RBAC Architecture

#### Role Hierarchy
```
Admin
  ├── Compliance Officer
  ├── Research Director
  │     ├── Senior Analyst
  │     │     └── Analyst
  │     └── Quantitative Analyst
  ├── API Developer
  └── Data Engineer
```

#### Permission Model

**Resource-Action Pattern**:
```
<resource>:<action>:<scope>

Examples:
- filings:read:own
- filings:read:organization
- filings:read:all
- signals:extract:own
- signals:validate:organization
- users:manage:organization
- api_keys:create:own
```

#### Database Schema

```sql
-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL,  -- Array of permission strings
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User roles (many-to-many)
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id),
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, role_id, organization_id)
);

-- Permission cache (for performance)
CREATE MATERIALIZED VIEW user_permissions AS
SELECT
    ur.user_id,
    ur.organization_id,
    r.permissions
FROM user_roles ur
JOIN roles r ON ur.role_id = r.id
WHERE ur.expires_at IS NULL OR ur.expires_at > NOW();

CREATE INDEX idx_user_permissions ON user_permissions(user_id, organization_id);
```

### 2.2 Permission Enforcement

#### FastAPI Dependency Injection

```python
from fastapi import Depends, HTTPException, status
from functools import wraps

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self,
                       request: Request,
                       current_user: User = Depends(get_current_user)):
        """Check if user has required permission"""
        # Get user permissions from cache/database
        permissions = await self.get_user_permissions(
            current_user.id,
            current_user.organization_id
        )

        # Check permission
        if not self.has_permission(permissions, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {self.required_permission}"
            )

        # Audit log
        await self.audit_log("permission_checked", {
            "user_id": current_user.id,
            "permission": self.required_permission,
            "granted": True,
            "ip_address": request.client.host
        })

        return current_user

    def has_permission(self, permissions: list, required: str) -> bool:
        """Check permission with wildcard support"""
        for perm in permissions:
            if self.match_permission(perm, required):
                return True
        return False

    def match_permission(self, granted: str, required: str) -> bool:
        """Match permission patterns (wildcards)"""
        granted_parts = granted.split(":")
        required_parts = required.split(":")

        if len(granted_parts) != len(required_parts):
            return False

        for g, r in zip(granted_parts, required_parts):
            if g != "*" and g != r:
                return False

        return True

# Usage in endpoints
@app.get("/api/v1/filings/{cik}")
async def get_filing(
    cik: str,
    user: User = Depends(PermissionChecker("filings:read:own"))
):
    """Get filing with permission check"""
    pass
```

#### Row-Level Security (Postgres)

```sql
-- Enable RLS on filings table
ALTER TABLE filings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see filings from their organization
CREATE POLICY filings_organization_access ON filings
    FOR SELECT
    USING (
        organization_id = current_setting('app.current_organization_id')::UUID
        OR
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = current_setting('app.current_user_id')::UUID
            AND r.permissions @> '["filings:read:all"]'::jsonb
        )
    );

-- Policy: Users can only create filings for their organization
CREATE POLICY filings_organization_insert ON filings
    FOR INSERT
    WITH CHECK (
        organization_id = current_setting('app.current_organization_id')::UUID
    );

-- Policy: Only admins can delete filings
CREATE POLICY filings_delete_admin ON filings
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = current_setting('app.current_user_id')::UUID
            AND r.name = 'Admin'
        )
    );
```

---

## 3. API Key Management

### 3.1 API Key Architecture

#### Key Generation

```python
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKeyManager:
    def generate_api_key(self, user_id: str, name: str,
                         scopes: list[str]) -> tuple[str, str]:
        """Generate API key pair (public prefix + secret)"""
        # Generate cryptographically secure random key
        key_bytes = secrets.token_bytes(32)

        # Create key with prefix for identification
        prefix = "slat"  # SEC Latent Analysis Token
        key_version = "v1"
        key_random = secrets.token_urlsafe(32)

        api_key = f"{prefix}_{key_version}_{key_random}"

        # Hash for storage (never store plaintext)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store in database
        key_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": f"{prefix}_{key_version}_{key_random[:8]}...",
            "name": name,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "last_used_at": None,
            "expires_at": datetime.utcnow() + timedelta(days=90),
            "rate_limit": 1000,  # requests per hour
            "is_active": True
        }

        await self.db.insert("api_keys", key_record)

        # Return full key (only shown once)
        return api_key, key_record["key_prefix"]

    async def validate_api_key(self, api_key: str) -> dict:
        """Validate API key and return metadata"""
        # Hash provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Lookup in database
        key_record = await self.db.query(
            "SELECT * FROM api_keys WHERE key_hash = $1 AND is_active = true",
            key_hash
        )

        if not key_record:
            raise SecurityError("Invalid API key")

        # Check expiration
        if key_record["expires_at"] < datetime.utcnow():
            raise SecurityError("API key expired")

        # Check rate limit
        if not await self.check_rate_limit(key_record["id"]):
            raise SecurityError("Rate limit exceeded")

        # Update last_used_at
        await self.db.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
            key_record["id"]
        )

        return key_record
```

### 3.2 Key Rotation Strategy

#### Automatic Rotation

```python
class KeyRotationPolicy:
    def __init__(self, db, notification_service):
        self.db = db
        self.notifications = notification_service

    async def check_rotation_required(self):
        """Check for keys requiring rotation"""
        # Find keys expiring in 7 days
        expiring_keys = await self.db.query("""
            SELECT * FROM api_keys
            WHERE expires_at < NOW() + INTERVAL '7 days'
            AND expires_at > NOW()
            AND is_active = true
        """)

        for key in expiring_keys:
            await self.notify_rotation_required(key)

    async def notify_rotation_required(self, key: dict):
        """Notify user of required key rotation"""
        user = await self.db.get_user(key["user_id"])

        await self.notifications.send_email(
            to=user["email"],
            subject="API Key Rotation Required",
            template="api_key_rotation",
            data={
                "key_name": key["name"],
                "key_prefix": key["key_prefix"],
                "expires_at": key["expires_at"],
                "rotation_url": f"/api-keys/rotate/{key['id']}"
            }
        )

    async def rotate_key(self, key_id: str, user_id: str) -> tuple[str, str]:
        """Rotate API key with grace period"""
        old_key = await self.db.get_api_key(key_id)

        # Verify ownership
        if old_key["user_id"] != user_id:
            raise SecurityError("Unauthorized")

        # Generate new key with same scopes
        new_key, new_prefix = await APIKeyManager().generate_api_key(
            user_id=user_id,
            name=old_key["name"],
            scopes=old_key["scopes"]
        )

        # Grace period: Old key remains valid for 7 days
        await self.db.execute("""
            UPDATE api_keys
            SET expires_at = NOW() + INTERVAL '7 days',
                is_rotated = true,
                rotated_to = $1
            WHERE id = $2
        """, new_key_id, key_id)

        return new_key, new_prefix
```

### 3.3 Rate Limiting

#### Token Bucket Algorithm

```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(self, key_id: str, limit: int,
                               window: int = 3600) -> bool:
        """Token bucket rate limiting"""
        bucket_key = f"rate_limit:{key_id}"

        # Get current tokens
        current = await self.redis.get(bucket_key)

        if current is None:
            # Initialize bucket
            await self.redis.setex(bucket_key, window, limit - 1)
            return True

        current = int(current)

        if current <= 0:
            # Rate limit exceeded
            await self.audit_log("rate_limit_exceeded", {
                "key_id": key_id,
                "limit": limit,
                "window": window
            })
            return False

        # Decrement tokens
        await self.redis.decr(bucket_key)
        return True
```

---

## 4. Encryption Standards

### 4.1 Encryption at Rest (AES-256)

#### Database Encryption

**PostgreSQL (Supabase)**:
```sql
-- Enable transparent data encryption
ALTER DATABASE sec_latent SET encrypt = on;

-- Encrypted column for sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE user_secrets (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    api_key_encrypted BYTEA,  -- Encrypted with AES-256
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Encrypt data on insert
INSERT INTO user_secrets (user_id, api_key_encrypted)
VALUES (
    'user_uuid',
    pgp_sym_encrypt('sensitive_api_key', current_setting('app.encryption_key'))
);

-- Decrypt on select
SELECT
    user_id,
    pgp_sym_decrypt(api_key_encrypted, current_setting('app.encryption_key')) as api_key
FROM user_secrets;
```

#### Application-Level Encryption

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

class DataEncryption:
    def __init__(self, encryption_key: bytes):
        """AES-256 encryption service"""
        self.key = encryption_key  # 32 bytes for AES-256
        if len(self.key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")

    def encrypt(self, plaintext: str) -> dict:
        """Encrypt data with AES-256-CBC"""
        # Generate random IV
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        # Pad plaintext to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        # Encrypt
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return {
            "ciphertext": ciphertext.hex(),
            "iv": iv.hex(),
            "algorithm": "AES-256-CBC"
        }

    def decrypt(self, ciphertext: str, iv: str) -> str:
        """Decrypt AES-256-CBC data"""
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(bytes.fromhex(iv)),
            backend=default_backend()
        )

        # Decrypt
        decryptor = cipher.decryptor()
        padded_plaintext = (
            decryptor.update(bytes.fromhex(ciphertext)) +
            decryptor.finalize()
        )

        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode()
```

### 4.2 Encryption in Transit (TLS 1.3)

#### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.sec-latent.com;

    # TLS 1.3 only
    ssl_protocols TLSv1.3;

    # Strong cipher suites
    ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256;
    ssl_prefer_server_ciphers off;

    # Certificate paths
    ssl_certificate /etc/letsencrypt/live/api.sec-latent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.sec-latent.com/privkey.pem;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/api.sec-latent.com/chain.pem;

    # HSTS (1 year)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # CSP (Content Security Policy)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.sec-latent.com;
    return 301 https://$server_name$request_uri;
}
```

#### Certificate Management

```python
class CertificateManager:
    """Automated certificate renewal with Let's Encrypt"""

    def __init__(self, domains: list[str], email: str):
        self.domains = domains
        self.email = email

    async def renew_certificates(self):
        """Renew certificates 30 days before expiration"""
        for domain in self.domains:
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"

            # Check expiration
            expiry = await self.get_certificate_expiry(cert_path)
            days_until_expiry = (expiry - datetime.utcnow()).days

            if days_until_expiry <= 30:
                logger.info(f"Renewing certificate for {domain}")
                await self.run_certbot_renewal(domain)
                await self.reload_nginx()
                await self.notify_renewal_complete(domain)

    async def run_certbot_renewal(self, domain: str):
        """Run certbot renewal"""
        cmd = [
            "certbot", "renew",
            "--domain", domain,
            "--email", self.email,
            "--non-interactive",
            "--agree-tos"
        ]

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            raise CertificateError(f"Renewal failed: {stderr.decode()}")
```

---

## 5. Anomaly Detection

### 5.1 ML-Based Threat Detection

#### Behavioral Anomaly Detection

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.01,  # 1% expected anomalies
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    async def train(self, historical_data: pd.DataFrame):
        """Train on normal behavior patterns"""
        # Feature engineering
        features = self.extract_features(historical_data)

        # Normalize
        features_scaled = self.scaler.fit_transform(features)

        # Train model
        self.model.fit(features_scaled)
        self.is_trained = True

        logger.info("Anomaly detector trained on %d samples", len(features))

    def extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract behavioral features"""
        features = []

        for user_id in data['user_id'].unique():
            user_data = data[data['user_id'] == user_id]

            features.append([
                # Request patterns
                user_data['requests_per_hour'].mean(),
                user_data['requests_per_hour'].std(),

                # Timing patterns
                user_data['request_hour'].mode()[0],
                user_data['requests_weekend'].sum() / len(user_data),

                # Resource access
                user_data['unique_endpoints'].nunique(),
                user_data['error_rate'].mean(),

                # Data volume
                user_data['bytes_transferred'].mean(),
                user_data['response_time'].mean(),

                # Geographic
                user_data['unique_ips'].nunique(),
                user_data['country_changes'].sum()
            ])

        return np.array(features)

    async def detect_anomaly(self, request_data: dict) -> dict:
        """Real-time anomaly detection"""
        if not self.is_trained:
            raise ValueError("Model not trained")

        # Extract features from current request
        features = self.extract_request_features(request_data)
        features_scaled = self.scaler.transform([features])

        # Predict
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.score_samples(features_scaled)[0]

        is_anomaly = prediction == -1
        confidence = abs(score)

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "risk_score": self.calculate_risk_score(features, score),
            "features": features,
            "timestamp": datetime.utcnow().isoformat()
        }

    def calculate_risk_score(self, features: list, anomaly_score: float) -> float:
        """Calculate risk score (0-100)"""
        # Normalize anomaly score to 0-100
        base_score = min(100, abs(anomaly_score) * 100)

        # Amplify based on high-risk features
        risk_multiplier = 1.0

        # Multiple IPs from different countries
        if features[8] > 3:  # unique_ips
            risk_multiplier *= 1.5

        # High error rate
        if features[5] > 0.1:  # error_rate
            risk_multiplier *= 1.3

        # Off-hours access
        if features[2] < 6 or features[2] > 22:  # request_hour
            risk_multiplier *= 1.2

        return min(100, base_score * risk_multiplier)
```

#### Real-Time Monitoring

```python
class ThreatMonitor:
    def __init__(self, anomaly_detector, alerting_service):
        self.detector = anomaly_detector
        self.alerts = alerting_service

    async def monitor_request(self, request: Request, user: User):
        """Monitor each request for anomalies"""
        # Collect request metadata
        request_data = {
            "user_id": user.id,
            "endpoint": request.url.path,
            "method": request.method,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow(),
            "response_time": 0  # Set after response
        }

        # Detect anomaly
        result = await self.detector.detect_anomaly(request_data)

        # Log to database
        await self.log_security_event({
            **request_data,
            **result
        })

        # Alert if high risk
        if result["risk_score"] > 80:
            await self.alerts.send_alert(
                level="CRITICAL",
                title="High-Risk Anomaly Detected",
                message=f"User {user.id} from {request.client.host}",
                data=result
            )

            # Temporary block if extremely suspicious
            if result["risk_score"] > 95:
                await self.temporary_block(user.id, duration=3600)

        return result
```

---

## 6. DDoS Protection

### 6.1 Multi-Layer Defense

#### Layer 1: CDN + WAF (Cloudflare)

```yaml
# Cloudflare configuration
security:
  waf:
    enabled: true
    managed_rules:
      - OWASP_ModSecurity_Core_Rule_Set
      - Cloudflare_Managed_Ruleset
    custom_rules:
      - name: "Block suspicious user agents"
        expression: "(http.user_agent contains 'bot' or http.user_agent contains 'crawler') and not http.user_agent contains 'Googlebot'"
        action: "block"

      - name: "Rate limit API endpoints"
        expression: "http.request.uri.path starts_with '/api/'"
        action: "rate_limit"
        rate_limit:
          requests: 100
          period: 60  # seconds

  ddos:
    enabled: true
    sensitivity: "high"
    l7_mitigation: true

  firewall_rules:
    - name: "Geo-blocking"
      expression: "ip.geoip.country not in {'US', 'GB', 'EU'}"
      action: "challenge"  # CAPTCHA

    - name: "Known bad IPs"
      expression: "ip.src in $known_bad_ips"
      action: "block"
```

#### Layer 2: Application Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

class AdaptiveRateLimiter:
    """Adaptive rate limiting based on user tier and behavior"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.tier_limits = {
            "free": {"requests": 100, "period": 3600},
            "basic": {"requests": 1000, "period": 3600},
            "pro": {"requests": 10000, "period": 3600},
            "enterprise": {"requests": 100000, "period": 3600}
        }

    async def check_rate_limit(self, user: User, endpoint: str) -> bool:
        """Adaptive rate limiting"""
        # Get base limit for user tier
        base_limit = self.tier_limits[user.tier]

        # Adjust based on recent behavior
        behavior_score = await self.get_behavior_score(user.id)

        if behavior_score < 0.5:  # Suspicious behavior
            adjusted_limit = int(base_limit["requests"] * 0.5)
        elif behavior_score > 0.9:  # Good behavior
            adjusted_limit = int(base_limit["requests"] * 1.2)
        else:
            adjusted_limit = base_limit["requests"]

        # Check limit
        key = f"rate_limit:{user.id}:{endpoint}"
        current = await self.redis.incr(key)

        if current == 1:
            await self.redis.expire(key, base_limit["period"])

        if current > adjusted_limit:
            await self.log_rate_limit_exceeded(user.id, endpoint)
            return False

        return True

# FastAPI integration
app = FastAPI()

@app.on_event("startup")
async def startup():
    redis_conn = redis.from_url("redis://localhost:6379")
    await FastAPILimiter.init(redis_conn)

@app.get("/api/v1/filings/{cik}")
@limiter.limit("100/minute")
async def get_filing(
    cik: str,
    user: User = Depends(get_current_user)
):
    """Rate-limited endpoint"""
    pass
```

#### Layer 3: Traffic Analysis

```python
class TrafficAnalyzer:
    """Real-time traffic analysis for DDoS detection"""

    def __init__(self, redis_client, threshold_multiplier=3.0):
        self.redis = redis_client
        self.threshold_multiplier = threshold_multiplier

    async def analyze_traffic(self, window: int = 60):
        """Analyze traffic patterns in sliding window"""
        current_time = int(time.time())
        window_start = current_time - window

        # Get requests in window
        requests = await self.redis.zrangebyscore(
            "traffic:requests",
            window_start,
            current_time
        )

        # Calculate metrics
        total_requests = len(requests)
        unique_ips = len(set(r["ip"] for r in requests))
        error_rate = sum(1 for r in requests if r["status"] >= 400) / total_requests

        # Get baseline
        baseline = await self.get_baseline_traffic()

        # Detect anomalies
        is_attack = False
        attack_type = None

        # Volume-based attack
        if total_requests > baseline["avg_requests"] * self.threshold_multiplier:
            is_attack = True
            attack_type = "volume"

        # Low diversity (single source)
        if unique_ips < 10 and total_requests > 1000:
            is_attack = True
            attack_type = "single_source"

        # High error rate (application layer)
        if error_rate > 0.5:
            is_attack = True
            attack_type = "application_layer"

        if is_attack:
            await self.trigger_mitigation(attack_type, {
                "total_requests": total_requests,
                "unique_ips": unique_ips,
                "error_rate": error_rate,
                "window": window
            })

        return {
            "is_attack": is_attack,
            "attack_type": attack_type,
            "metrics": {
                "total_requests": total_requests,
                "unique_ips": unique_ips,
                "error_rate": error_rate
            }
        }

    async def trigger_mitigation(self, attack_type: str, metrics: dict):
        """Trigger DDoS mitigation"""
        logger.critical(f"DDoS attack detected: {attack_type}", extra=metrics)

        # Activate aggressive rate limiting
        await self.activate_emergency_mode()

        # Alert security team
        await self.send_alert("ddos_attack_detected", {
            "type": attack_type,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Enable CAPTCHA for suspicious IPs
        await self.enable_captcha_challenge()
```

---

## 7. Compliance Framework

### 7.1 SOC 2 Type II Compliance

#### Control Implementation

**Access Controls (CC6.1)**:
- Multi-factor authentication (MFA) required for all users
- Role-based access control (RBAC) with least privilege
- Annual access reviews and recertification
- Automated access provisioning and deprovisioning

**Logical and Physical Access (CC6.2)**:
```python
class AccessControl:
    async def grant_access(self, user_id: str, resource: str,
                           justification: str, duration: int):
        """Grant temporary access with justification"""
        # Require approval for sensitive resources
        if self.is_sensitive_resource(resource):
            approval = await self.request_approval(
                user_id=user_id,
                resource=resource,
                justification=justification,
                duration=duration
            )

            if not approval.approved:
                raise AccessDeniedError("Approval required")

        # Grant with expiration
        access_grant = {
            "user_id": user_id,
            "resource": resource,
            "granted_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=duration),
            "granted_by": approval.approver_id if approval else "system",
            "justification": justification
        }

        await self.db.insert("access_grants", access_grant)

        # Audit log
        await self.audit_log("access_granted", access_grant)

        return access_grant
```

**Change Management (CC8.1)**:
```python
class ChangeManagement:
    async def deploy_change(self, change_request: dict):
        """Controlled change deployment"""
        # Require approvals
        if not change_request.get("approvals"):
            raise ValidationError("Change requires approvals")

        # Verify testing completed
        if not change_request.get("testing_completed"):
            raise ValidationError("Testing not completed")

        # Create rollback plan
        rollback_plan = await self.create_rollback_plan(change_request)

        # Deploy with monitoring
        deployment = await self.execute_deployment(
            change_request,
            rollback_plan
        )

        # Audit log
        await self.audit_log("change_deployed", {
            "change_id": change_request["id"],
            "deployment_id": deployment["id"],
            "deployed_by": change_request["deployed_by"],
            "timestamp": datetime.utcnow()
        })

        return deployment
```

### 7.2 FINRA Compliance

#### Books and Records (Rule 4511)

```python
class ComplianceRecords:
    """FINRA-compliant record keeping"""

    async def create_audit_record(self, event_type: str, data: dict):
        """Create immutable audit record"""
        record = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow(),
            "user_id": data.get("user_id"),
            "organization_id": data.get("organization_id"),
            "data": data,
            "hash": None  # Computed below
        }

        # Compute cryptographic hash for integrity
        record["hash"] = self.compute_record_hash(record)

        # Store in write-once storage
        await self.immutable_storage.insert(record)

        # Replicate to compliance archive
        await self.compliance_archive.replicate(record)

        return record

    def compute_record_hash(self, record: dict) -> str:
        """Compute SHA-256 hash of record"""
        # Create deterministic JSON
        record_json = json.dumps(
            {k: v for k, v in record.items() if k != "hash"},
            sort_keys=True
        )

        return hashlib.sha256(record_json.encode()).hexdigest()

    async def verify_record_integrity(self, record_id: str) -> bool:
        """Verify record has not been tampered with"""
        record = await self.immutable_storage.get(record_id)

        stored_hash = record["hash"]
        computed_hash = self.compute_record_hash(record)

        return stored_hash == computed_hash
```

#### Supervision and Review (Rule 3110)

```python
class SupervisionSystem:
    """Automated supervision and review"""

    async def monitor_trading_signals(self):
        """Monitor for suspicious trading patterns"""
        # Get recent signal extractions
        signals = await self.db.query("""
            SELECT s.*, f.cik, f.filing_date, u.user_id
            FROM signals s
            JOIN filings f ON s.filing_id = f.id
            JOIN users u ON s.extracted_by = u.id
            WHERE s.extracted_at > NOW() - INTERVAL '24 hours'
        """)

        for signal in signals:
            # Check for potential insider trading indicators
            if self.is_suspicious_pattern(signal):
                await self.flag_for_review(signal, "potential_insider_trading")

            # Check for market manipulation patterns
            if self.is_manipulation_pattern(signal):
                await self.flag_for_review(signal, "potential_manipulation")

    async def flag_for_review(self, signal: dict, reason: str):
        """Flag activity for compliance review"""
        review_case = {
            "id": str(uuid.uuid4()),
            "signal_id": signal["id"],
            "user_id": signal["user_id"],
            "reason": reason,
            "status": "pending_review",
            "created_at": datetime.utcnow(),
            "assigned_to": None
        }

        await self.db.insert("compliance_reviews", review_case)

        # Alert compliance team
        await self.notify_compliance_team(review_case)
```

### 7.3 GDPR/CCPA Compliance

#### Data Subject Rights

```python
class DataPrivacy:
    """GDPR/CCPA data subject rights"""

    async def handle_data_access_request(self, user_id: str) -> dict:
        """Right to access (GDPR Art. 15, CCPA 1798.110)"""
        # Collect all personal data
        data = {
            "user_profile": await self.get_user_profile(user_id),
            "api_keys": await self.get_user_api_keys(user_id),
            "audit_logs": await self.get_user_audit_logs(user_id),
            "filings_accessed": await self.get_user_filing_history(user_id),
            "signals_extracted": await self.get_user_signals(user_id)
        }

        # Log request
        await self.audit_log("data_access_request", {
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        })

        # Return in machine-readable format
        return {
            "format": "JSON",
            "data": data,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def handle_data_deletion_request(self, user_id: str):
        """Right to erasure (GDPR Art. 17, CCPA 1798.105)"""
        # Verify no legal hold
        if await self.has_legal_hold(user_id):
            raise ComplianceError("Cannot delete: legal hold active")

        # Anonymize user data
        await self.anonymize_user_data(user_id)

        # Delete personal identifiers
        await self.delete_user_profile(user_id)

        # Retain audit trail (compliance requirement)
        await self.audit_log("data_deletion_request", {
            "user_id": user_id,
            "anonymized_id": hashlib.sha256(user_id.encode()).hexdigest(),
            "timestamp": datetime.utcnow()
        })

    async def anonymize_user_data(self, user_id: str):
        """Anonymize user data while retaining analytics"""
        anonymized_id = hashlib.sha256(user_id.encode()).hexdigest()

        # Update audit logs
        await self.db.execute("""
            UPDATE audit_logs
            SET user_id = $1,
                personal_data_removed = true
            WHERE user_id = $2
        """, anonymized_id, user_id)

        # Update signal extraction records
        await self.db.execute("""
            UPDATE signals
            SET extracted_by = $1
            WHERE extracted_by = $2
        """, anonymized_id, user_id)
```

#### Data Processing Agreement

```python
class DataProcessingAgreement:
    """GDPR Art. 28 DPA requirements"""

    async def log_data_processing(self, activity: dict):
        """Record of processing activities (GDPR Art. 30)"""
        processing_record = {
            "activity_id": str(uuid.uuid4()),
            "purpose": activity["purpose"],
            "legal_basis": activity["legal_basis"],
            "data_categories": activity["data_categories"],
            "data_subjects": activity["data_subjects"],
            "recipients": activity.get("recipients", []),
            "retention_period": activity["retention_period"],
            "security_measures": activity["security_measures"],
            "timestamp": datetime.utcnow()
        }

        await self.db.insert("processing_records", processing_record)

        return processing_record
```

---

## 8. Audit Trail Architecture

### 8.1 Comprehensive Audit Logging

```python
class AuditLogger:
    """Centralized audit logging system"""

    def __init__(self, db, immutable_storage):
        self.db = db
        self.storage = immutable_storage

    async def log(self, event_type: str, user_id: Optional[str],
                  data: dict, severity: str = "INFO"):
        """Create audit log entry"""
        # Build audit record
        record = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "user_id": user_id,
            "organization_id": data.get("organization_id"),
            "severity": severity,
            "timestamp": datetime.utcnow(),
            "ip_address": data.get("ip_address"),
            "user_agent": data.get("user_agent"),
            "resource": data.get("resource"),
            "action": data.get("action"),
            "result": data.get("result", "success"),
            "details": json.dumps(data),
            "hash": None
        }

        # Compute integrity hash
        record["hash"] = self.compute_hash(record)

        # Write to immutable storage
        await self.storage.append(record)

        # Index in searchable database
        await self.db.insert("audit_logs", {
            **record,
            "indexed_at": datetime.utcnow()
        })

        # Alert on security events
        if severity in ["WARNING", "ERROR", "CRITICAL"]:
            await self.send_security_alert(record)

        return record["id"]

    async def search_audit_logs(self, filters: dict,
                                limit: int = 100) -> list:
        """Search audit logs with filters"""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if filters.get("user_id"):
            query += " AND user_id = $%d" % (len(params) + 1)
            params.append(filters["user_id"])

        if filters.get("event_type"):
            query += " AND event_type = $%d" % (len(params) + 1)
            params.append(filters["event_type"])

        if filters.get("start_date"):
            query += " AND timestamp >= $%d" % (len(params) + 1)
            params.append(filters["start_date"])

        if filters.get("end_date"):
            query += " AND timestamp <= $%d" % (len(params) + 1)
            params.append(filters["end_date"])

        query += " ORDER BY timestamp DESC LIMIT $%d" % (len(params) + 1)
        params.append(limit)

        results = await self.db.query(query, *params)

        # Verify integrity
        for result in results:
            if not await self.verify_integrity(result):
                logger.error(f"Audit log integrity violation: {result['id']}")

        return results
```

### 8.2 Data Lineage Tracking

```python
class DataLineage:
    """Track data provenance and transformations"""

    async def track_signal_extraction(self, filing_id: str,
                                      signal_data: dict):
        """Track complete lineage of signal extraction"""
        lineage = {
            "lineage_id": str(uuid.uuid4()),
            "entity_type": "signal",
            "entity_id": signal_data["id"],
            "created_at": datetime.utcnow(),
            "lineage_chain": []
        }

        # Source: SEC filing
        lineage["lineage_chain"].append({
            "step": 1,
            "operation": "source",
            "entity_type": "filing",
            "entity_id": filing_id,
            "source": "SEC EDGAR",
            "timestamp": signal_data["filing_date"]
        })

        # Transformation: parsing
        lineage["lineage_chain"].append({
            "step": 2,
            "operation": "parse",
            "method": "html_parser",
            "version": "1.0.0",
            "timestamp": signal_data["parsed_at"]
        })

        # Transformation: model inference
        lineage["lineage_chain"].append({
            "step": 3,
            "operation": "extract",
            "model": signal_data["model_used"],
            "model_version": signal_data["model_version"],
            "confidence": signal_data["confidence"],
            "timestamp": signal_data["extracted_at"]
        })

        # Transformation: validation
        if signal_data.get("validated_at"):
            lineage["lineage_chain"].append({
                "step": 4,
                "operation": "validate",
                "validator": "FACT_GOALIE",
                "validation_result": signal_data["validation_result"],
                "timestamp": signal_data["validated_at"]
            })

        # Store lineage
        await self.db.insert("data_lineage", lineage)

        return lineage["lineage_id"]
```

---

## 9. Security Monitoring & Incident Response

### 9.1 SIEM Integration

```python
class SecurityMonitoring:
    """Security Information and Event Management"""

    def __init__(self, elasticsearch_client, alerting_service):
        self.es = elasticsearch_client
        self.alerts = alerting_service

    async def ingest_security_event(self, event: dict):
        """Ingest security event into SIEM"""
        # Enrich event
        enriched_event = await self.enrich_event(event)

        # Index in Elasticsearch
        await self.es.index(
            index=f"security-events-{datetime.utcnow().strftime('%Y.%m')}",
            document=enriched_event
        )

        # Check for correlation with other events
        correlations = await self.find_correlations(enriched_event)

        if correlations:
            await self.trigger_correlation_alert(enriched_event, correlations)

    async def find_correlations(self, event: dict) -> list:
        """Find correlated security events"""
        # Search for related events in last hour
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"gte": "now-1h"}}},
                        {
                            "bool": {
                                "should": [
                                    {"term": {"user_id": event["user_id"]}},
                                    {"term": {"ip_address": event["ip_address"]}}
                                ]
                            }
                        }
                    ]
                }
            }
        }

        results = await self.es.search(
            index="security-events-*",
            body=query
        )

        return results["hits"]["hits"]
```

### 9.2 Automated Incident Response

```python
class IncidentResponse:
    """Automated incident response system"""

    async def handle_security_incident(self, incident: dict):
        """Automated incident response"""
        # Classify incident
        classification = self.classify_incident(incident)

        # Execute playbook
        playbook = self.get_playbook(classification["type"])

        for step in playbook["steps"]:
            await self.execute_response_step(step, incident)

        # Create incident ticket
        ticket = await self.create_incident_ticket(
            classification,
            incident,
            playbook["steps"]
        )

        return ticket

    def get_playbook(self, incident_type: str) -> dict:
        """Get incident response playbook"""
        playbooks = {
            "brute_force_attack": {
                "steps": [
                    {"action": "block_ip", "duration": 3600},
                    {"action": "reset_user_password", "require_mfa": True},
                    {"action": "notify_user", "template": "security_alert"},
                    {"action": "alert_security_team", "priority": "high"}
                ]
            },
            "data_exfiltration": {
                "steps": [
                    {"action": "block_user", "duration": "indefinite"},
                    {"action": "revoke_api_keys"},
                    {"action": "quarantine_data"},
                    {"action": "alert_security_team", "priority": "critical"},
                    {"action": "alert_compliance_team"}
                ]
            },
            "privilege_escalation": {
                "steps": [
                    {"action": "block_user", "duration": 86400},
                    {"action": "audit_user_permissions"},
                    {"action": "rollback_permissions"},
                    {"action": "alert_security_team", "priority": "critical"}
                ]
            }
        }

        return playbooks.get(incident_type, playbooks["brute_force_attack"])
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Sprint 1-2)
**Priority: CRITICAL**

1. **Authentication & Authorization**
   - JWT implementation with RS256
   - Refresh token rotation
   - Basic RBAC structure
   - API key generation and validation

2. **Encryption**
   - TLS 1.3 certificate setup
   - Database encryption at rest
   - Secret management (HashiCorp Vault)

3. **Audit Logging**
   - Basic audit trail
   - Immutable log storage
   - Compliance log retention

**Deliverables**:
- Working JWT authentication system
- Encrypted API endpoints
- Audit log infrastructure

### Phase 2: Protection (Sprint 3-4)
**Priority: HIGH**

1. **Rate Limiting & DDoS**
   - Token bucket rate limiting
   - Cloudflare WAF integration
   - Traffic analysis system

2. **Input Validation**
   - Request validation middleware
   - SQL injection prevention
   - XSS protection

3. **Monitoring**
   - Security event logging
   - Basic anomaly detection
   - Alert system

**Deliverables**:
- Rate-limited API
- Input validation framework
- Security monitoring dashboard

### Phase 3: Intelligence (Sprint 5-6)
**Priority: MEDIUM**

1. **Anomaly Detection**
   - ML-based behavioral analysis
   - Real-time threat detection
   - Automated response system

2. **Advanced RBAC**
   - Fine-grained permissions
   - Row-level security
   - Permission caching

3. **Compliance**
   - SOC 2 control implementation
   - FINRA record keeping
   - GDPR data subject rights

**Deliverables**:
- AI-powered threat detection
- Complete RBAC system
- Compliance framework

### Phase 4: Optimization (Sprint 7-8)
**Priority: LOW**

1. **Performance**
   - Security operation caching
   - Token validation optimization
   - Database query optimization

2. **Advanced Features**
   - Biometric authentication (optional)
   - Hardware security keys
   - Zero-trust architecture

3. **Documentation**
   - Security runbooks
   - Incident response procedures
   - Compliance documentation

**Deliverables**:
- Optimized security operations
- Complete documentation
- Production-ready platform

---

## 11. Risk Mitigation Matrix

| Risk | Likelihood | Impact | Mitigation | Priority |
|------|-----------|---------|------------|----------|
| API key leakage | HIGH | CRITICAL | Key rotation, monitoring, alerts | P0 |
| SQL injection | MEDIUM | CRITICAL | Parameterized queries, input validation | P0 |
| DDoS attack | HIGH | HIGH | CDN, rate limiting, traffic analysis | P0 |
| Insider threat | LOW | CRITICAL | RBAC, audit logs, anomaly detection | P1 |
| Data breach | MEDIUM | CRITICAL | Encryption, access controls, monitoring | P0 |
| Compliance violation | MEDIUM | HIGH | Automated compliance checks, audits | P1 |
| JWT compromise | MEDIUM | HIGH | Short expiration, token rotation | P0 |
| Brute force | HIGH | MEDIUM | Rate limiting, MFA, account lockout | P1 |
| Session hijacking | MEDIUM | HIGH | HttpOnly cookies, CSRF tokens | P1 |
| MITM attack | LOW | CRITICAL | TLS 1.3, certificate pinning | P0 |

---

## 12. Security Metrics & KPIs

### Operational Metrics
- **Authentication success rate**: >99.5%
- **Token validation latency**: <10ms
- **Rate limit false positives**: <0.1%
- **Anomaly detection accuracy**: >95%
- **Incident response time**: <15 minutes

### Compliance Metrics
- **Audit log completeness**: 100%
- **Data retention compliance**: 100%
- **Access review completion**: 100% quarterly
- **Security training completion**: 100% annually

### Security Posture
- **Vulnerability remediation time**: <7 days (critical), <30 days (high)
- **Penetration test pass rate**: 100%
- **Security audit findings**: 0 critical, <5 high
- **Uptime with security controls**: >99.9%

---

## 13. Conclusion

This comprehensive security architecture provides enterprise-grade protection for the SEC Latent Signal Analysis Platform. Implementation of these recommendations will:

1. **Protect sensitive financial data** with military-grade encryption
2. **Prevent unauthorized access** through robust authentication and RBAC
3. **Detect and respond to threats** using ML-based anomaly detection
4. **Ensure regulatory compliance** with SOC 2, FINRA, SEC, and GDPR
5. **Maintain audit trails** for complete data lineage and accountability

### Next Steps

1. **Architecture Review**: Review with security team and stakeholders
2. **Implementation Planning**: Create detailed sprint plans for Phase 1-4
3. **Resource Allocation**: Assign security specialists to each component
4. **Third-Party Audits**: Schedule SOC 2 and penetration testing
5. **Training**: Conduct security awareness training for all developers

---

**Document Owner**: Security Research Agent
**Review Cycle**: Quarterly
**Next Review**: 2025-11-18
**Classification**: INTERNAL USE ONLY

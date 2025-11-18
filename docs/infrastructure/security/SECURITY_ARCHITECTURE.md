# Security Architecture

## Overview

Comprehensive security architecture for the SEC Latent platform implementing defense-in-depth strategy with multiple security layers.

## Security Layers

```
┌────────────────────── Security Layers ──────────────────────┐
│                                                               │
│  Layer 1: Perimeter Security (CloudFlare WAF)               │
│  ├─ DDoS Protection                                          │
│  ├─ Bot Detection                                            │
│  ├─ Rate Limiting                                            │
│  └─ Geo-blocking                                             │
│                                                               │
│  Layer 2: Network Security                                   │
│  ├─ VPC Isolation                                            │
│  ├─ Security Groups                                          │
│  ├─ Private Subnets                                          │
│  └─ Firewall Rules                                           │
│                                                               │
│  Layer 3: Application Security                               │
│  ├─ OAuth 2.0 + JWT                                          │
│  ├─ API Key Management                                       │
│  ├─ Input Validation                                         │
│  └─ XSS/CSRF Protection                                      │
│                                                               │
│  Layer 4: Data Security                                      │
│  ├─ Encryption at Rest (AES-256)                            │
│  ├─ Encryption in Transit (TLS 1.3)                         │
│  ├─ Database Encryption                                      │
│  └─ Secrets Management                                       │
│                                                               │
│  Layer 5: Monitoring & Response                              │
│  ├─ SIEM (Security Information and Event Management)        │
│  ├─ Intrusion Detection                                      │
│  ├─ Audit Logging (7-year retention)                        │
│  └─ Incident Response                                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Network Security Architecture

### VPC Design

```
┌─────────────────────── VPC (10.0.0.0/16) ───────────────────────┐
│                                                                   │
│  ┌──────────────── Public Subnet (10.0.1.0/24) ───────────────┐ │
│  │                                                              │ │
│  │  ┌──────────────┐         ┌──────────────┐                │ │
│  │  │ Load Balancer│         │   Bastion    │                │ │
│  │  │   (Public)   │         │     Host     │                │ │
│  │  └──────┬───────┘         └──────────────┘                │ │
│  │         │                                                   │ │
│  └─────────┼───────────────────────────────────────────────────┘ │
│            │                                                      │
│  ┌─────────▼────── Private Subnet (10.0.2.0/24) ──────────────┐ │
│  │                                                              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │ │
│  │  │ Frontend │  │ Backend  │  │  Worker  │                 │ │
│  │  └──────────┘  └──────────┘  └──────────┘                 │ │
│  │                                                              │ │
│  └──────────────────────────┬───────────────────────────────────┘ │
│                             │                                      │
│  ┌──────────────────────────▼─── Data Subnet (10.0.3.0/24) ────┐ │
│  │                                                               │ │
│  │  ┌──────────────┐              ┌────────────────┐           │ │
│  │  │  PostgreSQL  │              │  Redis Cluster │           │ │
│  │  │   Private    │              │    Private     │           │ │
│  │  └──────────────┘              └────────────────┘           │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

              ┌────────────┐
              │  Internet  │
              └──────┬─────┘
                     │
         ┌───────────▼──────────────┐
         │   CloudFlare CDN/WAF     │
         └───────────┬──────────────┘
                     │ HTTPS Only
                     │
         ┌───────────▼──────────────┐
         │   Internet Gateway       │
         └──────────────────────────┘
```

### Security Groups

**Load Balancer Security Group**:
```yaml
Inbound:
  - Port 443 (HTTPS): 0.0.0.0/0
  - Port 80 (HTTP): 0.0.0.0/0 (redirect to 443)

Outbound:
  - Port 8000 (Backend): 10.0.2.0/24
  - Port 3000 (Frontend): 10.0.2.0/24
```

**Application Security Group**:
```yaml
Inbound:
  - Port 8000: From Load Balancer SG
  - Port 3000: From Load Balancer SG
  - Port 22 (SSH): From Bastion SG only

Outbound:
  - Port 5432 (PostgreSQL): 10.0.3.0/24
  - Port 6379 (Redis): 10.0.3.0/24
  - Port 443 (HTTPS): 0.0.0.0/0 (API calls)
```

**Database Security Group**:
```yaml
Inbound:
  - Port 5432: From Application SG only
  - Port 6379: From Application SG only

Outbound:
  - None (no internet access)
```

## Authentication & Authorization

### OAuth 2.0 + JWT Flow

```
┌──────┐                                  ┌──────────┐
│Client│                                  │OAuth     │
│      │                                  │Provider  │
└───┬──┘                                  │(Auth0)   │
    │                                     └────┬─────┘
    │ 1. Initiate OAuth                        │
    │─────────────────────────────────────────>│
    │                                           │
    │ 2. User authenticates                     │
    │<──────────────────────────────────────────│
    │                                           │
    │ 3. Authorization code                     │
    │<──────────────────────────────────────────│
    │                                           │
┌───▼──┐  4. Exchange code for token      ┌────▼─────┐
│Client│─────────────────────────────────>│Backend   │
│      │                                   │API       │
│      │  5. Access token + Refresh token  │          │
│      │<──────────────────────────────────│          │
│      │                                   │          │
│      │  6. API requests with JWT         │          │
│      │─────────────────────────────────>│          │
│      │                                   │          │
│      │  7. Validate JWT & respond        │          │
│      │<──────────────────────────────────│          │
└──────┘                                   └──────────┘
```

### JWT Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id-123"
  },
  "payload": {
    "sub": "user-123",
    "email": "user@example.com",
    "role": "analyst",
    "iat": 1697720000,
    "exp": 1697806400,
    "iss": "https://sec-latent.com",
    "aud": "https://api.sec-latent.com",
    "scopes": ["read:filings", "write:analysis"]
  },
  "signature": "..."
}
```

### Role-Based Access Control (RBAC)

```python
class Role:
    VIEWER = "viewer"       # Read-only access
    ANALYST = "analyst"     # Read + analyze
    ADMIN = "admin"         # Full access
    SUPERADMIN = "superadmin"  # System admin

class Permission:
    READ_FILINGS = "read:filings"
    WRITE_FILINGS = "write:filings"
    DELETE_FILINGS = "delete:filings"
    READ_ANALYSIS = "read:analysis"
    WRITE_ANALYSIS = "write:analysis"
    MANAGE_USERS = "manage:users"
    SYSTEM_ADMIN = "system:admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: [
        Permission.READ_FILINGS,
        Permission.READ_ANALYSIS
    ],
    Role.ANALYST: [
        Permission.READ_FILINGS,
        Permission.WRITE_FILINGS,
        Permission.READ_ANALYSIS,
        Permission.WRITE_ANALYSIS
    ],
    Role.ADMIN: [
        Permission.READ_FILINGS,
        Permission.WRITE_FILINGS,
        Permission.DELETE_FILINGS,
        Permission.READ_ANALYSIS,
        Permission.WRITE_ANALYSIS,
        Permission.MANAGE_USERS
    ],
    Role.SUPERADMIN: [Permission.SYSTEM_ADMIN]  # All permissions
}
```

### API Key Authentication

```python
import hashlib
import secrets

def generate_api_key() -> tuple[str, str]:
    """Generate API key and hash"""
    # Generate random key
    key = f"sec_{''.join(secrets.token_urlsafe(32))}"

    # Hash for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    return key, key_hash

def validate_api_key(provided_key: str, stored_hash: str) -> bool:
    """Validate API key against stored hash"""
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return secrets.compare_digest(provided_hash, stored_hash)
```

## Data Encryption

### Encryption at Rest

**PostgreSQL Encryption**:
```sql
-- Enable pgcrypto extension
CREATE EXTENSION pgcrypto;

-- Encrypt column
ALTER TABLE sensitive_data
ADD COLUMN encrypted_ssn BYTEA;

-- Insert encrypted data
INSERT INTO sensitive_data (encrypted_ssn)
VALUES (pgp_sym_encrypt('123-45-6789', '${ENCRYPTION_KEY}'));

-- Query encrypted data
SELECT pgp_sym_decrypt(encrypted_ssn, '${ENCRYPTION_KEY}')
FROM sensitive_data;
```

**File Encryption**:
```python
from cryptography.fernet import Fernet

class FileEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt_file(self, input_path: str, output_path: str):
        with open(input_path, 'rb') as f:
            data = f.read()

        encrypted = self.cipher.encrypt(data)

        with open(output_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_file(self, input_path: str, output_path: str):
        with open(input_path, 'rb') as f:
            encrypted = f.read()

        decrypted = self.cipher.decrypt(encrypted)

        with open(output_path, 'wb') as f:
            f.write(decrypted)
```

### Encryption in Transit

**TLS 1.3 Configuration** (nginx.conf):
```nginx
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256';
ssl_prefer_server_ciphers off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

## Input Validation & Sanitization

```python
from pydantic import BaseModel, validator, Field
import bleach

class FilingRequest(BaseModel):
    cik: str = Field(..., regex=r'^\d{10}$')
    filing_type: str = Field(..., regex=r'^(10-K|10-Q|8-K|DEF 14A)$')
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')

    @validator('*')
    def sanitize_html(cls, v):
        if isinstance(v, str):
            return bleach.clean(v, strip=True)
        return v

class AnalysisRequest(BaseModel):
    filing_id: int = Field(..., gt=0)
    analysis_type: str = Field(..., regex=r'^(financial|sentiment|risk)$')
    parameters: dict = Field(default_factory=dict)

    @validator('parameters')
    def validate_parameters(cls, v):
        # Limit nested depth
        if isinstance(v, dict):
            def check_depth(obj, depth=0):
                if depth > 3:
                    raise ValueError("Nested depth exceeds limit")
                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, depth + 1)
            check_depth(v)
        return v
```

## Rate Limiting

### Application-Level Rate Limiting

```python
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/filings/{filing_id}")
@limiter.limit("100/minute")
async def get_filing(request: Request, filing_id: int):
    """Rate limited endpoint"""
    pass

# API key-based rate limiting
def get_api_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(401, "API key required")
    return api_key

@app.get("/analysis/{filing_id}")
@limiter.limit("1000/hour", key_func=get_api_key)
async def analyze_filing(request: Request, filing_id: int):
    """Higher limit for API key users"""
    pass
```

### CloudFlare Rate Limiting Rules

```yaml
# cloudflare-rate-limits.yaml
rate_limits:
  - id: "global_rate_limit"
    threshold: 100
    period: 60
    action: challenge
    match:
      request:
        url: "api.sec-latent.com/*"

  - id: "api_endpoint_limit"
    threshold: 1000
    period: 3600
    action: block
    match:
      request:
        url: "api.sec-latent.com/api/*"

  - id: "auth_endpoint_limit"
    threshold: 5
    period: 60
    action: block
    match:
      request:
        url: "api.sec-latent.com/auth/*"
```

## Security Headers

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sec-latent.com", "https://www.sec-latent.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["sec-latent.com", "*.sec-latent.com"]
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.sec-latent.com"
    )

    return response
```

## Secrets Management

### Railway Secrets

```bash
# Set secrets via Railway CLI
railway variables set POSTGRES_PASSWORD=$(openssl rand -hex 32)
railway variables set REDIS_PASSWORD=$(openssl rand -hex 32)
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)
railway variables set ENCRYPTION_KEY=$(openssl rand -hex 32)

# Reference secrets in code
import os
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
```

### AWS Secrets Manager (Alternative)

```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> dict:
    """Retrieve secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret: {e}")

# Usage
db_creds = get_secret('sec-latent/production/database')
DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@..."
```

## Audit Logging

### Comprehensive Audit Trail

```python
from datetime import datetime
from typing import Optional

class AuditLogger:
    def __init__(self, db_session):
        self.db = db_session

    def log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        ip_address: str,
        user_agent: str,
        request_method: str,
        request_path: str,
        status_code: int,
        response_time_ms: int,
        metadata: Optional[dict] = None
    ):
        """Log user action to audit table"""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
            response_time_ms=response_time_ms,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        self.db.add(audit_entry)
        self.db.commit()

# Middleware for automatic audit logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)

    # Extract user from JWT
    user_id = get_user_from_token(request)

    # Log action
    audit_logger.log_action(
        user_id=user_id,
        action=f"{request.method} {request.url.path}",
        resource_type="api_endpoint",
        resource_id=None,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        request_method=request.method,
        request_path=request.url.path,
        status_code=response.status_code,
        response_time_ms=response_time_ms
    )

    return response
```

## Vulnerability Scanning

### Docker Image Scanning

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -f docker/Dockerfile.backend -t backend:latest .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'backend:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Fail on critical vulnerabilities
        run: |
          if grep -q "CRITICAL" trivy-results.sarif; then
            echo "Critical vulnerabilities found!"
            exit 1
          fi
```

### SAST (Static Application Security Testing)

```yaml
# .github/workflows/sast.yml
name: SAST Scan

on:
  push:
    branches: [main]

jobs:
  bandit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Bandit
        run: pip install bandit

      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
```

## Incident Response Plan

### Security Incident Classification

| Severity | Definition | Response Time | Example |
|----------|-----------|---------------|---------|
| Critical | Active breach, data loss | Immediate | Database compromised |
| High | Potential breach, vulnerability | < 1 hour | SQL injection detected |
| Medium | Security weakness | < 4 hours | Weak password policy |
| Low | Best practice violation | < 24 hours | Missing security header |

### Incident Response Workflow

```
┌─────────────┐
│  Detection  │
└──────┬──────┘
       │
┌──────▼──────┐
│ Assessment  │
└──────┬──────┘
       │
┌──────▼──────┐
│ Containment │
└──────┬──────┘
       │
┌──────▼──────┐
│ Eradication │
└──────┬──────┘
       │
┌──────▼──────┐
│  Recovery   │
└──────┬──────┘
       │
┌──────▼──────┐
│Post-Mortem  │
└─────────────┘
```

### Incident Response Playbook

**1. Detection**
- Automated alerts from SIEM
- Manual reporting
- Security scan findings

**2. Assessment**
- Determine scope and severity
- Identify affected systems
- Estimate impact

**3. Containment**
- Isolate affected systems
- Revoke compromised credentials
- Block malicious IPs
- Enable maintenance mode if needed

**4. Eradication**
- Remove malware/backdoors
- Patch vulnerabilities
- Update firewall rules
- Rotate all credentials

**5. Recovery**
- Restore from clean backups
- Verify system integrity
- Monitor for anomalies
- Gradual service restoration

**6. Post-Mortem**
- Root cause analysis
- Timeline reconstruction
- Lessons learned
- Prevention measures

## Compliance

### SEC Rule 17a-4 Compliance

**Requirements**:
- 7-year retention for audit logs
- Immutable storage (WORM - Write Once Read Many)
- Tamper-proof logs
- Rapid retrieval capability

**Implementation**:
```python
# Append-only audit logs with cryptographic verification
class ImmutableAuditLog:
    def __init__(self):
        self.previous_hash = "0" * 64

    def log_entry(self, entry: dict) -> str:
        """Create tamper-proof log entry"""
        entry['previous_hash'] = self.previous_hash
        entry['timestamp'] = datetime.utcnow().isoformat()

        # Calculate hash of current entry
        entry_json = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_json.encode()).hexdigest()

        entry['hash'] = current_hash
        self.previous_hash = current_hash

        # Store in database
        self.store_entry(entry)

        return current_hash

    def verify_chain(self) -> bool:
        """Verify integrity of audit log chain"""
        entries = self.get_all_entries()
        previous_hash = "0" * 64

        for entry in entries:
            # Verify previous hash matches
            if entry['previous_hash'] != previous_hash:
                return False

            # Recalculate hash
            entry_copy = entry.copy()
            stored_hash = entry_copy.pop('hash')
            entry_json = json.dumps(entry_copy, sort_keys=True)
            calculated_hash = hashlib.sha256(entry_json.encode()).hexdigest()

            if calculated_hash != stored_hash:
                return False

            previous_hash = stored_hash

        return True
```

### GDPR Compliance

**Data Subject Rights**:
```python
class GDPRCompliance:
    def right_to_access(self, user_id: str) -> dict:
        """Export all user data"""
        pass

    def right_to_erasure(self, user_id: str) -> None:
        """Delete user data (right to be forgotten)"""
        pass

    def right_to_rectification(self, user_id: str, updates: dict) -> None:
        """Update incorrect user data"""
        pass

    def right_to_portability(self, user_id: str) -> dict:
        """Export data in machine-readable format"""
        pass
```

## Security Checklist

- [ ] TLS 1.3 enabled for all communications
- [ ] Strong password policy enforced
- [ ] Multi-factor authentication enabled
- [ ] API keys rotated every 90 days
- [ ] Database encryption at rest enabled
- [ ] Automated backups configured and tested
- [ ] Vulnerability scanning in CI/CD pipeline
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Audit logging enabled (7-year retention)
- [ ] Incident response plan documented
- [ ] Security training completed
- [ ] Penetration testing scheduled
- [ ] Compliance requirements verified
- [ ] Disaster recovery plan tested

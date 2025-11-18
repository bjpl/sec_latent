# Security Testing Documentation

## Overview

Comprehensive security testing suite for the SEC Latent Analysis platform. This document describes penetration testing procedures, security test organization, and remediation guidelines.

## Security Test Suites

### 1. SQL Injection Tests (`test_sql_injection.py`)

**Purpose**: Detect and prevent SQL injection vulnerabilities

**Test Coverage**:
- Basic SQL injection payloads
- Union-based SQL injection
- Boolean-based blind SQL injection
- Time-based blind SQL injection
- Stacked queries
- DuckDB-specific injection
- Second-order SQL injection
- Parameter validation

**Critical Tests**:
```python
# CIK parameter injection
test_search_filings_cik_injection()

# Company name injection
test_search_filings_company_name_injection()

# Form type injection
test_search_filings_form_type_injection()

# Accession number path parameter
test_get_filing_accession_number_injection()
```

**Running Tests**:
```bash
pytest tests/security/test_sql_injection.py -v
```

### 2. XSS Vulnerability Tests (`test_xss_vulnerabilities.py`)

**Purpose**: Prevent Cross-Site Scripting attacks

**Test Coverage**:
- Reflected XSS
- Stored XSS
- DOM-based XSS
- HTML5 XSS vectors
- CSS-based XSS
- Filter bypass techniques
- XSS in WebSocket messages
- Content Security Policy validation

**Critical Tests**:
```python
# Company name XSS
test_search_filings_xss_in_company_name()

# Filing analysis response XSS
test_filing_analysis_xss_in_response()

# WebSocket broadcast XSS
test_websocket_broadcast_xss()

# Filter bypass attempts
test_filter_bypass_techniques()
```

**Running Tests**:
```bash
pytest tests/security/test_xss_vulnerabilities.py -v
```

### 3. Authentication Bypass Tests (`test_authentication_bypass.py`)

**Purpose**: Validate authentication and authorization controls

**Test Coverage**:
- Missing authentication checks
- Authentication header bypass
- Session fixation
- JWT vulnerabilities (none algorithm, algorithm confusion)
- Expired token validation
- JWT payload manipulation
- Horizontal privilege escalation
- Vertical privilege escalation
- IDOR (Insecure Direct Object Reference)
- API key vulnerabilities

**Critical Tests**:
```python
# JWT none algorithm attack
test_jwt_none_algorithm()

# JWT algorithm confusion
test_jwt_algorithm_confusion()

# Privilege escalation
test_horizontal_privilege_escalation()
test_vertical_privilege_escalation()

# IDOR
test_insecure_direct_object_reference()
```

**Running Tests**:
```bash
pytest tests/security/test_authentication_bypass.py -v
```

### 4. API Security Tests (`test_api_security.py`)

**Purpose**: Test API-specific security vulnerabilities

**Test Coverage**:
- Rate limiting enforcement
- CORS configuration
- CSRF protection
- Parameter tampering
- Mass assignment
- Input validation
- Error handling
- Security headers
- Cache security

**Critical Tests**:
```python
# Rate limiting
test_rate_limit_enforcement()

# CORS misconfiguration
test_cors_wildcard_origin()
test_cors_credentials_with_wildcard()

# Parameter tampering
test_mass_assignment()
test_parameter_pollution()

# Security headers
test_security_headers_presence()
```

**Running Tests**:
```bash
pytest tests/security/test_api_security.py -v
```

### 5. WebSocket Security Tests (`test_websocket_security.py`)

**Purpose**: Test WebSocket-specific vulnerabilities

**Test Coverage**:
- Connection limit enforcement
- WebSocket authentication
- Origin validation
- XSS in messages
- JSON injection
- Message flooding
- Connection spam
- Slowloris attacks
- Resource exhaustion

**Critical Tests**:
```python
# Connection security
test_websocket_connection_limit()
test_websocket_origin_validation()

# Message security
test_websocket_xss_in_messages()
test_websocket_json_injection()

# DoS protection
test_websocket_message_flooding()
test_websocket_slowloris_attack()
```

**Running Tests**:
```bash
pytest tests/security/test_websocket_security.py -v
```

### 6. Secrets Scanning Tests (`test_secrets_scanning.py`)

**Purpose**: Detect hardcoded secrets and credential exposure

**Test Coverage**:
- AWS credentials
- API keys
- Database credentials
- Private keys
- JWT secrets
- Environment variable security
- API response secrets
- Log sanitization

**Critical Tests**:
```python
# Hardcoded secrets detection
test_no_hardcoded_secrets_in_code()

# Environment security
test_env_file_not_committed()
test_required_env_vars_documented()

# Response sanitization
test_error_responses_no_secrets()
test_health_endpoint_no_secrets()
```

**Running Tests**:
```bash
pytest tests/security/test_secrets_scanning.py -v
```

### 7. DDoS Resilience Tests (`test_ddos_resilience.py`)

**Purpose**: Test Denial of Service resilience

**Test Coverage**:
- Rate limiting per endpoint
- Rate limiting by IP
- Resource exhaustion protection
- Connection exhaustion
- Cache exploitation
- Database DoS
- Application-layer DoS
- ReDoS (Regular Expression DoS)

**Critical Tests**:
```python
# Rate limiting
test_rate_limit_enforcement()
test_rate_limit_by_ip()

# Resource protection
test_memory_exhaustion_protection()
test_cpu_exhaustion_protection()

# DoS attacks
test_json_parsing_dos()
test_regex_dos()
```

**Running Tests**:
```bash
pytest tests/security/test_ddos_resilience.py -v
```

### 8. Infrastructure Security Tests (`test_infrastructure_security.py`)

**Purpose**: Test infrastructure and deployment security

**Test Coverage**:
- Dependency vulnerabilities
- Container security
- SSL/TLS configuration
- Network security
- File system security
- Server configuration
- Third-party integrations

**Critical Tests**:
```python
# Dependencies
test_no_known_vulnerable_packages()
test_dependency_versions_pinned()

# Container security
test_dockerfile_security_best_practices()
test_docker_compose_security()

# Network security
test_cors_configuration()
test_no_open_redirects()

# File system
test_no_directory_traversal()
```

**Running Tests**:
```bash
pytest tests/security/test_infrastructure_security.py -v
```

### 9. Compliance Audit Tests (`test_compliance_audit.py`)

**Purpose**: Validate compliance and audit trail

**Test Coverage**:
- Audit trail completeness
- Data retention policies
- Privacy compliance (GDPR, CCPA)
- Security compliance
- Financial compliance
- API compliance
- Incident response

**Critical Tests**:
```python
# Audit logging
test_api_access_logged()
test_authentication_attempts_logged()
test_data_modification_logged()

# Privacy compliance
test_consent_management()
test_right_to_access()
test_right_to_erasure()

# Security compliance
test_password_requirements()
test_encryption_standards()
```

**Running Tests**:
```bash
pytest tests/security/test_compliance_audit.py -v
```

## Running All Security Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run with coverage
pytest tests/security/ --cov=src --cov-report=html

# Run specific test class
pytest tests/security/test_sql_injection.py::TestSQLInjectionFilings -v

# Run and generate report
pytest tests/security/ -v --html=security_report.html --self-contained-html
```

## Penetration Testing Procedures

### 1. Pre-Test Preparation

**Scope Definition**:
- Define test boundaries
- Identify critical systems
- List test endpoints
- Document expected behavior

**Environment Setup**:
```bash
# Set up test environment
export ENVIRONMENT=testing
export DEBUG=False

# Start test database
docker-compose up -d test-db

# Run application in test mode
uvicorn src.api.main:app --reload --port 8001
```

### 2. Automated Security Scanning

**Run Automated Tests**:
```bash
# Full security test suite
pytest tests/security/ -v --tb=short

# Specific vulnerability class
pytest tests/security/test_sql_injection.py -v
pytest tests/security/test_xss_vulnerabilities.py -v
pytest tests/security/test_authentication_bypass.py -v
```

**Dependency Scanning**:
```bash
# Install security tools
pip install safety bandit

# Scan dependencies
safety check

# Scan code for security issues
bandit -r src/ -ll
```

**SAST (Static Application Security Testing)**:
```bash
# Run static analysis
bandit -r src/ -f json -o security_scan.json

# Check for secrets
git secrets --scan

# Lint security issues
flake8 src/ --select=S
```

### 3. Manual Penetration Testing

**SQL Injection Testing**:
1. Test all input parameters with SQL payloads
2. Verify error messages don't leak database info
3. Test second-order SQL injection
4. Verify parameterized queries are used

**XSS Testing**:
1. Test all input fields with XSS payloads
2. Verify output encoding
3. Test stored XSS in database
4. Check CSP headers

**Authentication Testing**:
1. Test authentication bypass techniques
2. Test session management
3. Test JWT vulnerabilities
4. Test privilege escalation

**API Security Testing**:
1. Test rate limiting
2. Test CORS configuration
3. Test input validation
4. Test error handling

### 4. Post-Test Reporting

**Document Findings**:
```markdown
## Vulnerability Report

### Critical Findings
1. [Title]: [Description]
   - Severity: Critical/High/Medium/Low
   - CVSS Score: X.X
   - Affected Component: [Component]
   - Reproduction Steps: [Steps]
   - Impact: [Impact]
   - Recommendation: [Fix]

### Medium Findings
[...]

### Low Findings
[...]

### Informational
[...]
```

## Security Vulnerability Remediation

### Severity Levels

**Critical** (CVSS 9.0-10.0):
- SQL Injection leading to data breach
- Remote Code Execution
- Authentication bypass
- **SLA**: Fix within 24 hours

**High** (CVSS 7.0-8.9):
- XSS in sensitive contexts
- Privilege escalation
- Sensitive data exposure
- **SLA**: Fix within 7 days

**Medium** (CVSS 4.0-6.9):
- CSRF vulnerabilities
- Information disclosure
- Missing security headers
- **SLA**: Fix within 30 days

**Low** (CVSS 0.1-3.9):
- Verbose error messages
- Weak password policy
- Missing rate limiting
- **SLA**: Fix within 90 days

### Remediation Process

1. **Triage**:
   - Assess severity
   - Verify reproducibility
   - Identify affected components

2. **Fix Development**:
   - Develop fix
   - Write regression test
   - Test in staging

3. **Deployment**:
   - Deploy to production
   - Verify fix
   - Update documentation

4. **Verification**:
   - Re-run security tests
   - Confirm vulnerability resolved
   - Update security documentation

## Security Best Practices

### Input Validation

```python
from pydantic import BaseModel, validator, Field

class SecureInput(BaseModel):
    cik: str = Field(..., regex=r"^\d{10}$")
    company_name: str = Field(..., max_length=200)

    @validator('company_name')
    def sanitize_company_name(cls, v):
        # Remove dangerous characters
        return v.replace('<', '').replace('>', '')
```

### Output Encoding

```python
from html import escape
import json

# HTML context
safe_html = escape(user_input)

# JSON context
safe_json = json.dumps(user_input)

# URL context
from urllib.parse import quote
safe_url = quote(user_input)
```

### Authentication

```python
from passlib.context import CryptContext
import jwt

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password)

# JWT tokens
token = jwt.encode(
    {"sub": user_id, "exp": expiry},
    SECRET_KEY,
    algorithm="HS256"
)
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/endpoint")
@limiter.limit("100/minute")
async def endpoint():
    return {"data": "response"}
```

## Security Testing Schedule

**Continuous**:
- Automated tests on every commit
- Dependency scanning daily

**Weekly**:
- Full security test suite
- SAST/DAST scans

**Monthly**:
- Manual penetration testing
- Security configuration review

**Quarterly**:
- Third-party security audit
- Compliance assessment

**Annually**:
- Comprehensive penetration test
- Security architecture review

## Security Tools

### Recommended Tools

**SAST** (Static Analysis):
- Bandit
- Semgrep
- SonarQube

**DAST** (Dynamic Analysis):
- OWASP ZAP
- Burp Suite
- Nikto

**Dependency Scanning**:
- Safety
- Snyk
- Dependabot

**Container Security**:
- Trivy
- Anchore
- Clair

**Secrets Detection**:
- git-secrets
- truffleHog
- detect-secrets

## Incident Response

### Security Incident Classification

**P0 - Critical**:
- Active data breach
- System compromise
- Remote code execution

**P1 - High**:
- Authentication bypass
- Privilege escalation
- Sensitive data exposure

**P2 - Medium**:
- XSS/CSRF vulnerabilities
- Information disclosure
- DoS attack

**P3 - Low**:
- Configuration issues
- Weak security controls
- Non-critical bugs

### Incident Response Steps

1. **Detection**: Identify security incident
2. **Containment**: Isolate affected systems
3. **Investigation**: Determine scope and impact
4. **Eradication**: Remove threat
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve

## Contact

**Security Team**: security@company.com
**Bug Bounty**: https://company.com/security
**Responsible Disclosure**: See SECURITY.md

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

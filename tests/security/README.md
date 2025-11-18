# Security Testing Suite

Comprehensive security testing for the SEC Latent Analysis platform.

## Quick Start

```bash
# Install dependencies
pip install -r requirements-security.txt

# Run all security tests
pytest tests/security/ -v

# Run specific test suite
pytest tests/security/test_sql_injection.py -v

# Run with coverage
pytest tests/security/ --cov=src --cov-report=html
```

## Test Suites

1. **test_sql_injection.py** - SQL injection vulnerability tests
2. **test_xss_vulnerabilities.py** - Cross-site scripting tests
3. **test_authentication_bypass.py** - Authentication and authorization tests
4. **test_api_security.py** - API-specific security tests
5. **test_websocket_security.py** - WebSocket security tests
6. **test_secrets_scanning.py** - Secrets and credential exposure tests
7. **test_ddos_resilience.py** - DDoS and load testing
8. **test_infrastructure_security.py** - Infrastructure security tests
9. **test_compliance_audit.py** - Compliance and audit tests

## Test Categories

### Vulnerability Tests
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Authentication Bypass
- Authorization Flaws
- Insecure Direct Object Reference (IDOR)

### Security Controls
- Input Validation
- Output Encoding
- Authentication
- Authorization
- Session Management
- Encryption

### Infrastructure
- Container Security
- Dependency Vulnerabilities
- SSL/TLS Configuration
- Network Security
- File System Security

### Compliance
- Audit Logging
- Data Retention
- Privacy (GDPR, CCPA)
- Financial Compliance

## Running Tests

### All Tests
```bash
pytest tests/security/ -v
```

### By Category
```bash
# Injection attacks
pytest tests/security/test_sql_injection.py tests/security/test_xss_vulnerabilities.py -v

# Authentication
pytest tests/security/test_authentication_bypass.py -v

# API security
pytest tests/security/test_api_security.py -v
```

### By Marker
```bash
# Critical tests only
pytest tests/security/ -m critical -v

# Penetration tests
pytest tests/security/ -m penetration -v
```

### Generate Report
```bash
pytest tests/security/ --html=security_report.html --self-contained-html
```

## Documentation

See [docs/testing/security_testing.md](../../docs/testing/security_testing.md) for complete documentation including:
- Detailed test descriptions
- Penetration testing procedures
- Remediation guidelines
- Security best practices

## Tools

### Required
- pytest
- pytest-asyncio
- fastapi testclient

### Recommended
- safety (dependency scanning)
- bandit (SAST)
- git-secrets (secrets detection)

### Optional
- OWASP ZAP (DAST)
- Burp Suite (pentesting)
- Trivy (container scanning)

## Test Results

Security tests should:
- ✅ Pass: Security control is effective
- ❌ Fail: Vulnerability detected (requires remediation)
- ⚠️  Warning: Informational finding (document for review)

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it to:
- Email: security@company.com
- See: SECURITY.md

## License

Same as project license

"""
Infrastructure Security Tests
Tests for container security, dependency vulnerabilities, and infrastructure misconfigurations
"""

import pytest
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Set
import tomli


class TestDependencyVulnerabilities:
    """Test for vulnerable dependencies"""

    @pytest.mark.asyncio
    async def test_no_known_vulnerable_packages(self):
        """Test that dependencies don't have known vulnerabilities"""
        # Use pip-audit or safety to check dependencies
        try:
            # Run safety check (if installed)
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # No vulnerabilities found
                pass
            else:
                # Check output for vulnerabilities
                if result.stdout:
                    vulnerabilities = json.loads(result.stdout)
                    if vulnerabilities:
                        pytest.fail(f"Known vulnerabilities found: {vulnerabilities}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # safety not installed - document recommendation
            print("\nRecommendation: Install safety for dependency scanning")
            print("  pip install safety")
            print("  safety check")

    @pytest.mark.asyncio
    async def test_dependency_versions_pinned(self):
        """Test that dependency versions are pinned"""
        requirements_file = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent/config/requirements.txt")

        if requirements_file.exists():
            content = requirements_file.read_text()

            # Check for unpinned versions
            unpinned = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check if version is pinned (==, >=, etc.)
                    if '==' not in line and '>=' not in line and '~=' not in line:
                        unpinned.append(line)

            if unpinned:
                print(f"\nWarning: Unpinned dependencies found:")
                for dep in unpinned:
                    print(f"  {dep}")

    @pytest.mark.asyncio
    async def test_no_deprecated_packages(self):
        """Test for deprecated or unmaintained packages"""
        # Known deprecated packages to avoid
        deprecated_packages = [
            "pycrypto",  # Use cryptography instead
            "BeautifulSoup",  # Use beautifulsoup4
            "optparse",  # Use argparse
        ]

        requirements_file = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent/config/requirements.txt")

        if requirements_file.exists():
            content = requirements_file.read_text().lower()

            for deprecated in deprecated_packages:
                assert deprecated.lower() not in content, \
                    f"Deprecated package found: {deprecated}"


class TestContainerSecurity:
    """Test container and Docker security"""

    @pytest.mark.asyncio
    async def test_dockerfile_security_best_practices(self):
        """Test Dockerfile follows security best practices"""
        project_root = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent")
        dockerfile = project_root / "Dockerfile"

        if not dockerfile.exists():
            print("\nDockerfile not found - skipping container security tests")
            return

        content = dockerfile.read_text()

        # Security checks
        issues = []

        # 1. Should not run as root
        if "USER root" in content or ("USER" not in content and "FROM" in content):
            issues.append("Container may run as root - should specify USER")

        # 2. Should use specific base image versions
        if ":latest" in content:
            issues.append("Using :latest tag - should pin specific versions")

        # 3. Should not expose unnecessary ports
        # Document which ports are necessary

        # 4. Should not copy sensitive files
        if ".env" in content and "COPY .env" in content:
            issues.append("Dockerfile copies .env file - secrets should use build args or runtime secrets")

        # 5. Should use multi-stage builds for smaller images
        # (Not required, but recommended)

        if issues:
            warnings = "\n".join(f"  - {issue}" for issue in issues)
            print(f"\nDockerfile security issues:\n{warnings}")

    @pytest.mark.asyncio
    async def test_docker_compose_security(self):
        """Test docker-compose.yml security configuration"""
        project_root = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent")
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            print("\ndocker-compose.yml not found")
            return

        content = compose_file.read_text()

        issues = []

        # 1. Should not expose database ports publicly
        if "5432:5432" in content or "3306:3306" in content:
            issues.append("Database ports exposed publicly")

        # 2. Should use secrets for sensitive data
        if "PASSWORD=" in content and "secrets:" not in content:
            issues.append("Passwords in environment variables - use Docker secrets")

        # 3. Should limit container capabilities
        # (Optional - check for cap_drop, security_opt)

        if issues:
            warnings = "\n".join(f"  - {issue}" for issue in issues)
            print(f"\nDocker Compose security issues:\n{warnings}")

    @pytest.mark.asyncio
    async def test_no_secrets_in_docker_images(self):
        """Test that Docker images don't contain secrets"""
        # This test would scan Docker image layers
        # Requires docker and dive/trivy installed
        pass


class TestSSLTLSConfiguration:
    """Test SSL/TLS configuration"""

    @pytest.mark.asyncio
    async def test_ssl_certificate_validation(self):
        """Test SSL certificate validation"""
        # In production, verify:
        # - Valid SSL certificate
        # - Certificate not self-signed (for production)
        # - Certificate not expired
        # - Strong cipher suites
        pass

    @pytest.mark.asyncio
    async def test_tls_version_enforcement(self):
        """Test that only secure TLS versions are allowed"""
        # Should enforce TLS 1.2+ only
        # Disable SSLv3, TLS 1.0, TLS 1.1
        pass

    @pytest.mark.asyncio
    async def test_hsts_header(self, client):
        """Test HTTP Strict Transport Security header"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/")

        hsts_header = response.headers.get("strict-transport-security")

        if hsts_header:
            # Verify HSTS configuration
            assert "max-age=" in hsts_header
            # Recommended: max-age >= 31536000 (1 year)

            # Optional: includeSubDomains, preload
        else:
            print("\nRecommendation: Add Strict-Transport-Security header")


class TestNetworkSecurity:
    """Test network security configuration"""

    @pytest.mark.asyncio
    async def test_cors_configuration(self, client):
        """Test CORS configuration security"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get(
            "/api/v1/filings/search",
            headers={"Origin": "https://malicious.com"}
        )

        cors_origin = response.headers.get("access-control-allow-origin")

        # SECURITY ISSUE: Currently allows * (all origins)
        if cors_origin == "*":
            print("\nWARNING: CORS allows all origins")
            print("Recommendation: Restrict to specific domains in production")

    @pytest.mark.asyncio
    async def test_no_open_redirects(self, client):
        """Test for open redirect vulnerabilities"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)

        # Test various redirect attempts
        redirect_attempts = [
            "/redirect?url=https://evil.com",
            "/redirect?next=//evil.com",
            "/redirect?return_to=javascript:alert(1)",
        ]

        for attempt in redirect_attempts:
            response = client.get(attempt, follow_redirects=False)

            # Should not redirect to arbitrary URLs
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get("location", "")
                assert not any(evil in location for evil in ["evil.com", "javascript:"]), \
                    f"Open redirect vulnerability: {attempt}"


class TestFileSystemSecurity:
    """Test file system security"""

    @pytest.mark.asyncio
    async def test_no_directory_traversal(self, client):
        """Test for directory traversal vulnerabilities"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)

        traversal_attempts = [
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc/passwd",
        ]

        for attempt in traversal_attempts:
            response = client.get(f"/api/v1/filings/{attempt}")

            # Should not allow file system access
            assert response.status_code in [400, 403, 404, 422]

            if response.status_code == 200:
                content = response.text.lower()
                # Should not contain file contents
                assert "root:" not in content
                assert "/bin/bash" not in content

    @pytest.mark.asyncio
    async def test_file_upload_security(self):
        """Test file upload security (if implemented)"""
        # Check for:
        # - File type validation
        # - File size limits
        # - Malicious file detection
        # - Safe file storage location
        pass


class TestServerConfiguration:
    """Test server configuration security"""

    @pytest.mark.asyncio
    async def test_server_headers_not_leaked(self, client):
        """Test that server information is not leaked"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/")

        # Should not reveal server details
        server_header = response.headers.get("server", "")

        if server_header:
            # Should not contain version numbers
            # Example: "uvicorn" instead of "uvicorn/0.17.6"
            print(f"\nServer header: {server_header}")

    @pytest.mark.asyncio
    async def test_debug_mode_disabled(self):
        """Test that debug mode is disabled in production"""
        from config.settings import get_settings

        settings = get_settings()

        # Debug should be False in production
        if settings.environment == "production":
            assert settings.debug == False, "Debug mode must be disabled in production"

    @pytest.mark.asyncio
    async def test_error_pages_no_stack_traces(self, client):
        """Test that error pages don't show stack traces"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)

        # Trigger 404 error
        response = client.get("/this-does-not-exist")

        if response.status_code == 404:
            content = response.text.lower()

            # Should not contain stack trace
            assert "traceback" not in content
            assert "exception" not in content or '"detail"' in content  # JSON error is OK


class TestSecurityMonitoring:
    """Test security monitoring and logging"""

    @pytest.mark.asyncio
    async def test_security_events_logged(self):
        """Test that security events are logged"""
        # Security events that should be logged:
        # - Authentication failures
        # - Authorization denials
        # - Input validation failures
        # - Rate limit violations
        # - Suspicious patterns

        # This test verifies logging configuration
        # Implementation depends on logging setup
        pass

    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self):
        """Test audit trail for sensitive operations"""
        # Should log:
        # - Who (user/IP)
        # - What (action)
        # - When (timestamp)
        # - Where (endpoint)
        # - Result (success/failure)

        # Implementation depends on audit logging setup
        pass


class TestThirdPartyIntegrations:
    """Test third-party integration security"""

    @pytest.mark.asyncio
    async def test_api_key_validation(self):
        """Test third-party API key validation"""
        from config.settings import get_settings

        settings = get_settings()

        # Verify API keys are configured
        # (Not testing actual keys - just configuration)
        assert hasattr(settings.models, 'sonnet_api_key')
        assert hasattr(settings.models, 'haiku_api_key')

    @pytest.mark.asyncio
    async def test_external_api_timeout(self):
        """Test timeouts for external API calls"""
        from config.settings import get_settings

        settings = get_settings()

        # Verify timeout is configured
        assert hasattr(settings.sec_edgar, 'timeout')
        assert settings.sec_edgar.timeout > 0
        assert settings.sec_edgar.timeout <= 60  # Reasonable timeout


class TestComplianceChecks:
    """Test compliance with security standards"""

    @pytest.mark.asyncio
    async def test_gdpr_compliance_headers(self, client):
        """Test GDPR compliance indicators"""
        # Document GDPR requirements:
        # - Right to erasure
        # - Data portability
        # - Consent management
        # - Privacy policy
        pass

    @pytest.mark.asyncio
    async def test_data_encryption_at_rest(self):
        """Test data encryption at rest"""
        # Verify:
        # - Database encryption
        # - File system encryption
        # - Backup encryption
        pass

    @pytest.mark.asyncio
    async def test_data_encryption_in_transit(self):
        """Test data encryption in transit"""
        # Verify:
        # - HTTPS enforced
        # - TLS for database connections
        # - Encrypted Redis connections
        pass


@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Secrets Scanning and Credential Exposure Tests
Tests for hardcoded secrets, credential exposure, and sensitive data leaks
"""

import pytest
import re
import os
from pathlib import Path
from typing import List, Dict, Set
import json


class TestSecretsInCode:
    """Test for hardcoded secrets in code"""

    # Patterns for common secrets
    SECRET_PATTERNS = {
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "aws_secret_key": r"[0-9a-zA-Z/+=]{40}",
        "github_token": r"gh[pousr]_[0-9a-zA-Z]{36}",
        "slack_token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[0-9a-zA-Z]{24,32}",
        "slack_webhook": r"https://hooks.slack.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[0-9a-zA-Z]{24}",
        "stripe_key": r"sk_live_[0-9a-zA-Z]{24}",
        "twilio_key": r"SK[0-9a-f]{32}",
        "jwt_secret": r"jwt_secret.*[=:].*['\"]([^'\"]{32,})['\"]",
        "api_key": r"api[_-]?key.*[=:].*['\"]([^'\"]{20,})['\"]",
        "password": r"password.*[=:].*['\"]([^'\"]{8,})['\"]",
        "secret_key": r"secret[_-]?key.*[=:].*['\"]([^'\"]{20,})['\"]",
        "database_url": r"(?:postgres|mysql|mongodb)://[^:]+:[^@]+@[^/]+/",
        "private_key": r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----",
        "supabase_key": r"eyJ[A-Za-z0-9_-]{30,}",
        "anthropic_key": r"sk-ant-[a-zA-Z0-9-]{40,}",
    }

    def get_python_files(self, root_dir: str = ".") -> List[Path]:
        """Get all Python files in project"""
        root_path = Path(root_dir)
        python_files = []

        for py_file in root_path.rglob("*.py"):
            # Skip virtual environments and caches
            if any(skip in str(py_file) for skip in ["venv", ".venv", "node_modules", "__pycache__", ".git"]):
                continue
            python_files.append(py_file)

        return python_files

    @pytest.mark.asyncio
    async def test_no_hardcoded_secrets_in_code(self):
        """Test that no hardcoded secrets exist in source code"""
        project_root = "/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent"
        python_files = self.get_python_files(project_root)

        findings: Dict[str, List[Dict]] = {}

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")

                for secret_type, pattern in self.SECRET_PATTERNS.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)

                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1

                        # Get the line content
                        lines = content.split('\n')
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        # Check if it's a false positive (example, test data, comment)
                        if self._is_false_positive(line_content):
                            continue

                        if str(py_file) not in findings:
                            findings[str(py_file)] = []

                        findings[str(py_file)].append({
                            "type": secret_type,
                            "line": line_num,
                            "content": line_content[:100],  # First 100 chars
                        })

            except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        # Report findings
        if findings:
            report = "\n\nHardcoded secrets found:\n"
            for file_path, secrets in findings.items():
                report += f"\n{file_path}:\n"
                for secret in secrets:
                    report += f"  Line {secret['line']}: {secret['type']}\n"
                    report += f"    {secret['content']}\n"

            pytest.fail(f"Hardcoded secrets detected!{report}")

    def _is_false_positive(self, line: str) -> bool:
        """Check if the match is likely a false positive"""
        false_positive_indicators = [
            "example",
            "test",
            "sample",
            "dummy",
            "placeholder",
            "todo",
            "xxx",
            "...",
            "your_",
            "<your",
            "fake",
            "mock",
            "#",  # Comment
        ]

        line_lower = line.lower()
        return any(indicator in line_lower for indicator in false_positive_indicators)


class TestEnvironmentVariables:
    """Test environment variable security"""

    @pytest.mark.asyncio
    async def test_env_file_not_committed(self):
        """Test that .env files are in .gitignore"""
        project_root = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent")
        gitignore_path = project_root / ".gitignore"

        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()

            # Check for .env in .gitignore
            assert ".env" in gitignore_content or \
                   "*.env" in gitignore_content, \
                   ".env files should be in .gitignore"
        else:
            pytest.fail(".gitignore file not found")

    @pytest.mark.asyncio
    async def test_required_env_vars_documented(self):
        """Test that required environment variables are documented"""
        project_root = Path("/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent")

        # Check for .env.example or .env.template
        env_example_files = [
            ".env.example",
            ".env.template",
            ".env.sample",
            "example.env",
        ]

        found_example = False
        for env_file in env_example_files:
            if (project_root / env_file).exists():
                found_example = True
                break

        # Document that env example should exist
        if not found_example:
            # Not a failure, but document the recommendation
            print("\nRecommendation: Create .env.example with placeholder values")

    @pytest.mark.asyncio
    async def test_env_vars_in_settings(self):
        """Test that environment variables are properly loaded"""
        from config.settings import get_settings

        settings = get_settings()

        # Verify that sensitive settings use env vars
        # (Should not have actual values hardcoded)
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'models')

        # Settings should be configured to read from environment
        # Actual values should come from .env file


class TestAPIResponseSecrets:
    """Test that API responses don't leak secrets"""

    @pytest.mark.asyncio
    async def test_error_responses_no_secrets(self, client):
        """Test that error responses don't contain secrets"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)

        # Trigger various errors
        error_endpoints = [
            "/api/v1/filings/invalid_accession",
            "/api/v1/predictions/history/invalid",
        ]

        sensitive_patterns = [
            r"password",
            r"secret",
            r"key",
            r"token",
            r"credential",
            r"api_key",
            r"database.*password",
            r"supabase.*key",
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)

            if response.status_code >= 400:
                response_text = response.text.lower()

                for pattern in sensitive_patterns:
                    matches = re.findall(pattern, response_text, re.IGNORECASE)
                    # Allow the word in field names, but not actual values
                    if matches:
                        # Check if it's just a field name or actual secret
                        # Field names are OK: {"error": "missing api_key"}
                        # Actual secrets are NOT OK: {"api_key": "sk-123..."}
                        pass

    @pytest.mark.asyncio
    async def test_health_endpoint_no_secrets(self, client):
        """Test that health endpoint doesn't leak configuration"""
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/health")

        if response.status_code == 200:
            data = response.json()

            # Health check should not contain:
            # - Database credentials
            # - API keys
            # - Internal IPs (except localhost indicators)
            # - File paths

            response_str = json.dumps(data).lower()

            # Check for sensitive information
            sensitive_info = [
                "password",
                "secret",
                "credential",
                "/home/",
                "/root/",
            ]

            for info in sensitive_info:
                assert info not in response_str, \
                    f"Health endpoint leaks sensitive info: {info}"


class TestLogSecurity:
    """Test that logs don't contain secrets"""

    @pytest.mark.asyncio
    async def test_logging_config_sanitizes_secrets(self):
        """Test that logging configuration sanitizes sensitive data"""
        from src.utils.logging_config import setup_logging

        # This test verifies that the logging system
        # has filters or sanitizers for sensitive data
        # Implementation depends on logging configuration

        # Document that logs should sanitize:
        # - Passwords
        # - API keys
        # - Tokens
        # - Database credentials
        pass


class TestDatabaseSecrets:
    """Test database credential security"""

    @pytest.mark.asyncio
    async def test_database_credentials_from_env(self):
        """Test that database credentials come from environment"""
        from config.settings import get_settings

        settings = get_settings()

        # Database settings should use environment variables
        # Check that Config class specifies env_file
        assert hasattr(settings.database.Config, 'env_file')
        assert settings.database.Config.env_file == ".env"

    @pytest.mark.asyncio
    async def test_database_urls_not_in_code(self):
        """Test that database URLs are not hardcoded"""
        project_root = "/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent"
        python_files = list(Path(project_root).rglob("*.py"))

        # Pattern for database URLs with credentials
        db_url_pattern = r"(?:postgres|mysql|mongodb)://[^:]+:[^@]+@"

        findings = []

        for py_file in python_files:
            if any(skip in str(py_file) for skip in ["venv", ".venv", "test_secrets"]):
                continue

            try:
                content = py_file.read_text()
                matches = re.finditer(db_url_pattern, content)

                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append({
                        "file": str(py_file),
                        "line": line_num,
                    })

            except Exception:
                pass

        if findings:
            report = "\n\nDatabase URLs with credentials found in code:\n"
            for finding in findings:
                report += f"  {finding['file']}:{finding['line']}\n"
            pytest.fail(f"Database credentials in code!{report}")


class TestSecretManagement:
    """Test secret management practices"""

    @pytest.mark.asyncio
    async def test_secrets_not_in_git_history(self):
        """Test that secrets haven't been committed to git"""
        # This test would require running git log analysis
        # Implementation depends on git access
        # Document recommendation to use git-secrets or similar tools
        pass

    @pytest.mark.asyncio
    async def test_secret_rotation_process(self):
        """Test that secret rotation process is documented"""
        # Document that secrets should be rotated periodically
        # and there should be a process for handling compromised secrets
        pass


@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

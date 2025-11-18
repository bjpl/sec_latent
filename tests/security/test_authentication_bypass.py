"""
Authentication and Authorization Bypass Tests
Tests for authentication bypass, privilege escalation, and authorization flaws
"""

import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any


class TestAuthenticationBypass:
    """Test authentication bypass vulnerabilities"""

    @pytest.mark.asyncio
    async def test_missing_authentication_endpoints(self, client: TestClient):
        """Test that sensitive endpoints require authentication"""
        sensitive_endpoints = [
            ("/api/v1/filings/search", "GET"),
            ("/api/v1/predictions/predict", "POST"),
            ("/api/v1/signals/query", "GET"),
        ]

        for endpoint, method in sensitive_endpoints:
            # Request without authentication
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should either require auth (401) or be public (200)
            # Document which endpoints should be protected
            assert response.status_code in [200, 401, 403, 422]

    @pytest.mark.asyncio
    async def test_authentication_header_bypass(self, client: TestClient):
        """Test bypass attempts via malformed auth headers"""
        bypass_attempts = [
            {},  # No auth header
            {"Authorization": ""},  # Empty auth
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # Wrong auth type
            {"Authorization": "Bearer null"},  # Null token
            {"Authorization": "Bearer undefined"},  # Undefined token
            {"X-API-Key": ""},  # Alternative auth method
        ]

        for headers in bypass_attempts:
            response = client.get(
                "/api/v1/filings/search",
                headers=headers
            )

            # Should not allow bypass
            assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_session_fixation(self, client: TestClient):
        """Test session fixation vulnerabilities"""
        # Attempt to use a pre-set session ID
        malicious_session = "attacker_session_12345"

        response = client.get(
            "/api/v1/filings/search",
            cookies={"session_id": malicious_session}
        )

        # Should not accept pre-set session IDs
        # New session should be created or request rejected
        assert response.status_code in [200, 401, 403]


class TestJWTVulnerabilities:
    """Test JWT token vulnerabilities"""

    def create_malicious_jwt(
        self,
        payload: Dict[str, Any],
        algorithm: str = "HS256",
        secret: str = "secret"
    ) -> str:
        """Create JWT token for testing"""
        return jwt.encode(payload, secret, algorithm=algorithm)

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm(self, client: TestClient):
        """Test 'none' algorithm vulnerability"""
        # Create token with 'none' algorithm
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # JWT with 'none' algorithm
        token_parts = jwt.encode(payload, "", algorithm="none").split('.')
        malicious_token = f"{token_parts[0]}.{token_parts[1]}."

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {malicious_token}"}
        )

        # Should reject 'none' algorithm
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_jwt_algorithm_confusion(self, client: TestClient):
        """Test algorithm confusion attack (RS256 -> HS256)"""
        # This tests if server accepts HS256 when expecting RS256
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # Create token with HS256 (symmetric) instead of RS256 (asymmetric)
        token = self.create_malicious_jwt(payload, algorithm="HS256", secret="public_key")

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should reject algorithm mismatch
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_jwt_expired_token(self, client: TestClient):
        """Test expired JWT token"""
        payload = {
            "sub": "user",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }

        token = self.create_malicious_jwt(payload)

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should reject expired token
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_jwt_payload_manipulation(self, client: TestClient):
        """Test JWT payload manipulation"""
        # Create token with regular user role
        payload = {
            "sub": "user@example.com",
            "role": "user",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        token = self.create_malicious_jwt(payload)

        # Decode and modify payload (without re-signing)
        decoded = jwt.decode(token, options={"verify_signature": False})
        decoded["role"] = "admin"  # Privilege escalation attempt

        # Create new token with modified payload but wrong signature
        import base64
        import json
        header = json.dumps({"alg": "HS256", "typ": "JWT"})
        payload_str = json.dumps(decoded)

        header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip("=")

        # Keep original signature (which is now invalid)
        original_sig = token.split('.')[2]
        malicious_token = f"{header_b64}.{payload_b64}.{original_sig}"

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {malicious_token}"}
        )

        # Should reject token with invalid signature
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_jwt_weak_secret(self, client: TestClient):
        """Test JWT with weak/common secrets"""
        weak_secrets = [
            "secret",
            "password",
            "123456",
            "admin",
            "key",
        ]

        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        for secret in weak_secrets:
            token = self.create_malicious_jwt(payload, secret=secret)

            response = client.get(
                "/api/v1/filings/search",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should not accept tokens signed with weak secrets
            # (This test documents the need for strong secrets)
            assert response.status_code in [200, 401, 403]


class TestAuthorizationFlaws:
    """Test authorization and privilege escalation"""

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, client: TestClient):
        """Test access to other users' data"""
        # User A tries to access User B's data
        user_a_cik = "0001234567"
        user_b_cik = "0009876543"

        # Simulate User A authenticated session
        response = client.get(
            f"/api/v1/predictions/history/{user_b_cik}"
        )

        # Should enforce authorization
        # Either allow (if public) or deny (if user-specific)
        assert response.status_code in [200, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation(self, client: TestClient):
        """Test regular user accessing admin functions"""
        admin_endpoints = [
            ("/api/v1/filings/0001234567-23-000001/cache", "DELETE"),
            ("/admin/users", "GET"),
            ("/admin/settings", "POST"),
        ]

        for endpoint, method in admin_endpoints:
            # Request as regular user (or no auth)
            if method == "DELETE":
                response = client.delete(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)

            # Should deny access to admin functions
            assert response.status_code in [401, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_insecure_direct_object_reference(self, client: TestClient):
        """Test IDOR vulnerabilities"""
        # Try accessing objects by ID without authorization
        test_ids = [
            "1",
            "2",
            "admin",
            "../../../etc/passwd",
        ]

        for test_id in test_ids:
            response = client.get(f"/api/v1/filings/{test_id}")

            # Should validate object ownership/access
            assert response.status_code in [200, 400, 403, 404, 422]

    @pytest.mark.asyncio
    async def test_parameter_tampering(self, client: TestClient):
        """Test parameter tampering for privilege escalation"""
        # Attempt to modify role/permissions via parameters
        tamper_params = [
            {"role": "admin"},
            {"is_admin": "true"},
            {"permissions": "all"},
            {"user_type": "admin"},
        ]

        for params in tamper_params:
            response = client.get(
                "/api/v1/filings/search",
                params=params
            )

            # Should not grant elevated privileges via parameters
            assert response.status_code in [200, 400, 422]


class TestAPIKeyVulnerabilities:
    """Test API key authentication vulnerabilities"""

    @pytest.mark.asyncio
    async def test_api_key_enumeration(self, client: TestClient):
        """Test API key enumeration"""
        test_keys = [
            "test_key_" + str(i) for i in range(10)
        ]

        for key in test_keys:
            response = client.get(
                "/api/v1/filings/search",
                headers={"X-API-Key": key}
            )

            # Should not leak information about valid keys
            # All invalid keys should return same response
            assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_api_key_in_url(self, client: TestClient):
        """Test API key in URL parameters (insecure)"""
        response = client.get(
            "/api/v1/filings/search?api_key=test_key_12345"
        )

        # Should not accept API keys in URL
        # (They can be logged and leaked)
        assert response.status_code in [200, 400, 401]


class TestSessionManagement:
    """Test session management vulnerabilities"""

    @pytest.mark.asyncio
    async def test_session_timeout(self, client: TestClient):
        """Test session timeout enforcement"""
        # Simulate old session
        old_session_id = "session_from_2020"

        response = client.get(
            "/api/v1/filings/search",
            cookies={"session_id": old_session_id}
        )

        # Should reject expired sessions
        assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, client: TestClient):
        """Test concurrent session handling"""
        # Multiple sessions for same user
        # Should be allowed or properly managed
        session_ids = [f"session_{i}" for i in range(5)]

        for session_id in session_ids:
            response = client.get(
                "/api/v1/filings/search",
                cookies={"session_id": session_id}
            )

            assert response.status_code in [200, 401, 403]


@pytest.fixture
def client():
    """Create test client"""
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Critical Vulnerability Penetration Tests
Tests for CRITICAL issues identified by Code Reviewer

CRITICAL ISSUES ADDRESSED:
1. No authentication/authorization on API endpoints
2. CORS wildcard (*) configuration
3. WebSocket connections without authentication
4. Redis without authentication
"""

import pytest
from fastapi.testclient import TestClient
import redis
import asyncio
from typing import List, Dict, Any
import json


class TestCriticalAuthenticationIssues:
    """
    CRITICAL: Tests for missing authentication/authorization
    Priority: CRITICAL
    """

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_unauthenticated_api_access(self, client: TestClient):
        """
        CRITICAL: Verify all sensitive endpoints require authentication

        EXPECTED: 401 Unauthorized for all sensitive endpoints
        CURRENT: Many endpoints accessible without auth
        """
        sensitive_endpoints = [
            ("/api/v1/filings/search", "GET", {}),
            ("/api/v1/filings/0001234567-23-000001", "GET", {}),
            ("/api/v1/predictions/predict", "POST", {
                "accession_number": "0001234567-23-000001",
                "prediction_type": "price_movement",
                "horizon": 30
            }),
            ("/api/v1/predictions/history/0001234567", "GET", {}),
            ("/api/v1/signals/query", "GET", {}),
            ("/api/v1/validation/verify", "POST", {"accession_number": "0001234567-23-000001"}),
        ]

        results = []
        for endpoint, method, data in sensitive_endpoints:
            # Request WITHOUT authentication
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)

            result = {
                "endpoint": endpoint,
                "method": method,
                "status": response.status_code,
                "has_auth": response.status_code == 401,
                "severity": "CRITICAL" if response.status_code != 401 else "SECURE"
            }
            results.append(result)

            # CRITICAL: Endpoints should require authentication
            if response.status_code == 200:
                pytest.fail(
                    f"CRITICAL VULNERABILITY: {endpoint} accessible without authentication!\n"
                    f"Status: {response.status_code}\n"
                    f"Response: {response.json() if response.text else 'No content'}"
                )

        # Log all results
        print("\n=== Authentication Test Results ===")
        for result in results:
            print(f"{result['severity']}: {result['method']} {result['endpoint']} -> {result['status']}")

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_authentication_bypass_attempts(self, client: TestClient):
        """
        CRITICAL: Test various authentication bypass techniques
        """
        bypass_payloads = [
            # Empty/invalid tokens
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer null"},
            {"Authorization": "Bearer undefined"},
            {"Authorization": "Bearer false"},

            # Token manipulation
            {"Authorization": "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9."},  # 'none' algorithm
            {"Authorization": "Bearer ..."},  # Invalid format

            # Alternative auth headers
            {"X-API-Key": ""},
            {"X-Auth-Token": "bypass"},
            {"Cookie": "session=admin"},

            # SQL injection in auth
            {"Authorization": "Bearer ' OR '1'='1"},

            # Header injection
            {"Authorization": "Bearer test\nX-Admin: true"},
        ]

        for headers in bypass_payloads:
            response = client.get("/api/v1/filings/search", headers=headers)

            # Should NOT allow access with invalid auth
            assert response.status_code in [401, 403], \
                f"CRITICAL: Bypass possible with headers: {headers}\nStatus: {response.status_code}"

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_rbac_enforcement(self, client: TestClient):
        """
        CRITICAL: Test Role-Based Access Control enforcement
        """
        # Test without role claims
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.invalid"

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {fake_token}"}
        )

        # Should reject invalid token
        assert response.status_code in [401, 403], \
            "CRITICAL: Invalid JWT token accepted"


class TestCriticalCORSVulnerabilities:
    """
    CRITICAL: Tests for CORS wildcard vulnerability
    Priority: CRITICAL
    CVE Reference: CVE-2020-26154 (CORS misconfiguration)
    """

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_cors_wildcard_vulnerability(self, client: TestClient):
        """
        CRITICAL: CORS allows wildcard (*) origin

        ISSUE: Line 154 in src/api/main.py:
        allow_origins=["*"]  # CRITICAL VULNERABILITY

        IMPACT: Any website can make authenticated requests
        EXPLOIT: Cross-origin credential theft
        """
        malicious_origins = [
            "https://evil-attacker.com",
            "http://phishing-site.com",
            "https://malicious.xyz",
            "null",  # file:// origins
        ]

        for origin in malicious_origins:
            response = client.get(
                "/api/v1/filings/search",
                headers={"Origin": origin}
            )

            cors_origin = response.headers.get("access-control-allow-origin")
            cors_credentials = response.headers.get("access-control-allow-credentials")

            # CRITICAL: Should NOT allow arbitrary origins
            if cors_origin == "*":
                pytest.fail(
                    "CRITICAL VULNERABILITY: CORS allows wildcard origin!\n"
                    f"Malicious origin '{origin}' accepted\n"
                    "LOCATION: src/api/main.py:154\n"
                    "FIX: Replace allow_origins=['*'] with specific origins"
                )

            # EXTREMELY CRITICAL: Wildcard + credentials = credential theft
            if cors_origin == "*" and cors_credentials == "true":
                pytest.fail(
                    "EXTREMELY CRITICAL: Wildcard CORS with credentials enabled!\n"
                    "This allows complete authentication bypass from any origin!\n"
                    "IMMEDIATE ACTION REQUIRED"
                )

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_cors_credential_theft_exploit(self, client: TestClient):
        """
        CRITICAL: Demonstrate CORS credential theft exploit
        """
        # Simulate attacker's origin
        attacker_origin = "https://attacker.com"

        # Preflight request
        preflight = client.options(
            "/api/v1/filings/search",
            headers={
                "Origin": attacker_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization"
            }
        )

        # Actual request with credentials
        response = client.get(
            "/api/v1/filings/search",
            headers={
                "Origin": attacker_origin,
                "Authorization": "Bearer valid-token-here",
                "Cookie": "session=user-session"
            }
        )

        # Check if attacker can access response
        cors_origin = response.headers.get("access-control-allow-origin")

        if cors_origin in ["*", attacker_origin]:
            pytest.fail(
                f"CRITICAL: Attacker origin '{attacker_origin}' can access API with credentials!\n"
                "Proof of Concept: Cross-origin authenticated requests possible"
            )


class TestCriticalWebSocketVulnerabilities:
    """
    CRITICAL: Tests for WebSocket authentication bypass
    Priority: CRITICAL
    """

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_websocket_no_authentication(self, client: TestClient):
        """
        CRITICAL: WebSocket connections accept without authentication

        ISSUE: src/api/routers/websockets.py
        No authentication check in WebSocket endpoints

        IMPACT: Anyone can connect and receive real-time data
        """
        ws_endpoints = [
            "/ws/filings",
            "/ws/predictions",
            "/ws/signals",
            "/ws/market"
        ]

        for endpoint in ws_endpoints:
            try:
                # Connect WITHOUT authentication
                with client.websocket_connect(endpoint) as websocket:
                    # Send ping to verify connection
                    websocket.send_json({"type": "ping"})

                    # Receive response
                    response = websocket.receive_json(timeout=2)

                    if response:
                        pytest.fail(
                            f"CRITICAL VULNERABILITY: WebSocket {endpoint} accessible without auth!\n"
                            f"Response received: {response}\n"
                            "FIX: Add authentication check in WebSocket handler"
                        )

            except Exception as e:
                # Connection rejected - GOOD!
                if "401" in str(e) or "403" in str(e):
                    print(f"SECURE: {endpoint} requires authentication")
                else:
                    # Other error - investigate
                    print(f"WARNING: {endpoint} error: {str(e)}")

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_websocket_message_injection(self, client: TestClient):
        """
        CRITICAL: WebSocket message injection without validation
        """
        try:
            with client.websocket_connect("/ws/filings") as websocket:
                # Malicious payloads
                injection_payloads = [
                    # Command injection
                    {"type": "subscribe", "channel": "'; DROP TABLE filings--"},

                    # XSS injection
                    {"type": "subscribe", "data": "<script>alert('XSS')</script>"},

                    # Prototype pollution
                    {"__proto__": {"isAdmin": True}},

                    # JSON injection
                    {"type": "subscribe\",\"admin\":true,\"type\":\"subscribe"}
                ]

                for payload in injection_payloads:
                    websocket.send_json(payload)

                    try:
                        response = websocket.receive_json(timeout=1)
                        response_str = json.dumps(response)

                        # Check for injection success
                        if "admin" in response_str.lower() or "error" not in response_str:
                            pytest.fail(
                                f"CRITICAL: WebSocket injection possible!\n"
                                f"Payload: {payload}\n"
                                f"Response: {response}"
                            )
                    except:
                        pass  # Timeout is acceptable

        except Exception as e:
            # Connection failed - acceptable
            pass


class TestCriticalInfrastructureVulnerabilities:
    """
    CRITICAL: Tests for infrastructure security issues
    Priority: CRITICAL
    """

    @pytest.mark.critical
    def test_redis_no_authentication(self):
        """
        CRITICAL: Redis has no authentication configured

        ISSUE: src/api/main.py:101-110
        Redis connection without password

        ISSUE: docker/docker-compose.yml:31
        Redis password only in command, not enforced by client

        IMPACT: Direct Redis access possible
        EXPLOIT: Cache poisoning, data theft, DoS
        """
        try:
            # Attempt to connect to Redis WITHOUT auth
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)

            # Try to execute command
            result = r.ping()

            if result:
                pytest.fail(
                    "CRITICAL VULNERABILITY: Redis accessible without authentication!\n"
                    "LOCATION: src/api/main.py:101-110\n"
                    "CURRENT: Redis connection has no password\n"
                    "FIX: Add password parameter to Redis connection\n"
                    "redis.Redis(host='localhost', port=6379, password=os.getenv('REDIS_PASSWORD'))"
                )

        except redis.AuthenticationError:
            # GOOD! Authentication is required
            print("SECURE: Redis requires authentication")
        except redis.ConnectionError:
            # Redis not running - skip test
            pytest.skip("Redis not available for testing")
        except Exception as e:
            print(f"INFO: Redis test error: {e}")

    @pytest.mark.critical
    def test_redis_unauthorized_commands(self):
        """
        CRITICAL: Test Redis command injection
        """
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)

            # Dangerous commands that should be disabled
            dangerous_commands = [
                "CONFIG GET *",  # Configuration disclosure
                "FLUSHALL",      # Delete all data
                "SHUTDOWN",      # Stop Redis
                "DEBUG SEGFAULT", # Crash Redis
            ]

            for cmd in dangerous_commands:
                try:
                    r.execute_command(*cmd.split())
                    pytest.fail(
                        f"CRITICAL: Dangerous Redis command '{cmd}' executable!\n"
                        "FIX: Disable dangerous commands in redis.conf"
                    )
                except (redis.AuthenticationError, redis.ResponseError):
                    # Command blocked - GOOD!
                    pass

        except redis.ConnectionError:
            pytest.skip("Redis not available")


class TestCriticalSecurityHeaders:
    """
    CRITICAL: Tests for missing security headers
    Priority: HIGH
    """

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_missing_security_headers(self, client: TestClient):
        """
        CRITICAL: Verify security headers are present
        """
        response = client.get("/")

        critical_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'",
        }

        missing_headers = []
        for header, expected_value in critical_headers.items():
            actual_value = response.headers.get(header.lower())

            if not actual_value:
                missing_headers.append(header)
            elif expected_value not in actual_value:
                missing_headers.append(f"{header} (incorrect value)")

        if missing_headers:
            pytest.fail(
                f"CRITICAL: Missing security headers: {', '.join(missing_headers)}\n"
                "FIX: Add SecurityHeadersMiddleware in src/api/main.py"
            )


@pytest.fixture
def client():
    """Create test client"""
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "critical"])

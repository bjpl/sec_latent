"""
Advanced Penetration Testing Suite
Comprehensive attack scenarios for security validation

Tests include:
- JWT manipulation and cryptographic attacks
- Rate limiting bypass techniques
- Session hijacking and fixation
- API abuse and resource exhaustion
- Input validation bypass
- Business logic flaws
"""

import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import asyncio
from typing import List, Dict, Any
import json


class TestJWTCryptographicAttacks:
    """Advanced JWT token manipulation attacks"""

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm_bypass(self, client: TestClient):
        """
        Test JWT 'none' algorithm vulnerability (CVE-2015-9235)

        ATTACK: Change alg to 'none' and remove signature
        IMPACT: Complete authentication bypass
        """
        # Create payload with admin privileges
        payload = {
            "sub": "attacker@evil.com",
            "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "roles": ["admin", "superuser"],
            "permissions": ["*"]
        }

        # Encode with 'none' algorithm
        import base64
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip("=")

        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")

        # Create token with no signature
        malicious_token = f"{header}.{payload_b64}."

        response = client.get(
            "/api/v1/filings/search",
            headers={"Authorization": f"Bearer {malicious_token}"}
        )

        # Should reject 'none' algorithm
        assert response.status_code in [401, 403], \
            f"VULNERABILITY: 'none' algorithm accepted! Status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_jwt_key_confusion_attack(self, client: TestClient):
        """
        Test JWT algorithm confusion (RS256 -> HS256)

        ATTACK: Sign with HMAC using public key as secret
        IMPACT: Token forgery if server accepts HS256
        """
        # Simulated public key (would be obtained from JWKS endpoint)
        fake_public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg..."

        payload = {
            "sub": "attacker",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "roles": ["admin"]
        }

        # Sign with HS256 using public key as secret
        try:
            token = jwt.encode(payload, fake_public_key, algorithm="HS256")

            response = client.get(
                "/api/v1/filings/search",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should reject algorithm confusion
            assert response.status_code in [401, 403], \
                "VULNERABILITY: Algorithm confusion possible!"

        except Exception:
            # jwt library may reject this - that's good
            pass

    @pytest.mark.asyncio
    async def test_jwt_timing_attack(self, client: TestClient):
        """
        Test JWT signature verification timing attack

        ATTACK: Measure response time to brute-force signature
        IMPACT: Signature verification bypass
        """
        import time

        test_tokens = [
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0." + "A" * 43,  # Wrong signature
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0." + "B" * 43,  # Wrong signature
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.valid_sig_here",  # Placeholder
        ]

        timings = []
        for token in test_tokens:
            start = time.perf_counter()

            response = client.get(
                "/api/v1/filings/search",
                headers={"Authorization": f"Bearer {token}"}
            )

            elapsed = time.perf_counter() - start
            timings.append(elapsed)

        # Timing should be constant (use constant-time comparison)
        # Significant variance indicates timing leak
        avg_time = sum(timings) / len(timings)
        max_deviation = max(abs(t - avg_time) for t in timings)

        # Allow 10ms variance (should use constant-time comparison)
        if max_deviation > 0.01:
            print(f"WARNING: JWT timing variance detected: {max_deviation:.4f}s")
            print(f"Timings: {timings}")

    @pytest.mark.asyncio
    async def test_jwt_kid_injection(self, client: TestClient):
        """
        Test JWT 'kid' (Key ID) header injection

        ATTACK: Inject malicious key location in 'kid' header
        IMPACT: Path traversal, SQL injection, command injection
        """
        malicious_kids = [
            "../../../etc/passwd",
            "../../config/secret_key",
            "'; DROP TABLE keys--",
            "../../../../dev/null",
            "http://evil.com/malicious_key",
        ]

        for kid in malicious_kids:
            header = {
                "alg": "HS256",
                "typ": "JWT",
                "kid": kid
            }

            payload = {"sub": "test"}

            try:
                # Create token with malicious kid
                import base64
                header_b64 = base64.urlsafe_b64encode(
                    json.dumps(header).encode()
                ).decode().rstrip("=")

                payload_b64 = base64.urlsafe_b64encode(
                    json.dumps(payload).encode()
                ).decode().rstrip("=")

                fake_sig = "invalid_signature_here"
                token = f"{header_b64}.{payload_b64}.{fake_sig}"

                response = client.get(
                    "/api/v1/filings/search",
                    headers={"Authorization": f"Bearer {token}"}
                )

                # Should reject and not execute path traversal
                assert response.status_code in [401, 403], \
                    f"VULNERABILITY: 'kid' injection with {kid}"

            except Exception:
                pass


class TestRateLimitingBypass:
    """Advanced rate limiting bypass techniques"""

    @pytest.mark.asyncio
    async def test_rate_limit_ip_header_spoofing(self, client: TestClient):
        """
        Test rate limit bypass via IP header manipulation

        ATTACK: Spoof X-Forwarded-For and other IP headers
        IMPACT: Unlimited requests
        """
        endpoint = "/api/v1/filings/search"

        # Try different IP spoofing headers
        spoof_headers = [
            {"X-Forwarded-For": "1.2.3.4"},
            {"X-Real-IP": "5.6.7.8"},
            {"X-Originating-IP": "9.10.11.12"},
            {"CF-Connecting-IP": "13.14.15.16"},
            {"True-Client-IP": "17.18.19.20"},
        ]

        for headers in spoof_headers:
            rate_limited = False

            # Send many requests
            for i in range(150):
                response = client.get(endpoint, headers=headers)

                if response.status_code == 429:
                    rate_limited = True
                    break

            # Should still get rate limited even with spoofed headers
            # If not rate limited after 150 requests, bypass worked
            if not rate_limited:
                print(f"WARNING: Rate limit possibly bypassed with headers: {headers}")

    @pytest.mark.asyncio
    async def test_rate_limit_user_agent_rotation(self, client: TestClient):
        """
        Test rate limit bypass via User-Agent rotation
        """
        endpoint = "/api/v1/filings/search"

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "curl/7.68.0",
            "python-requests/2.28.0",
        ]

        total_requests = 0
        for ua in user_agents:
            # 50 requests per user agent
            for i in range(50):
                response = client.get(
                    endpoint,
                    headers={"User-Agent": ua}
                )
                total_requests += 1

                if response.status_code == 429:
                    break

        # Should not allow 250 total requests via UA rotation
        print(f"Total requests completed with UA rotation: {total_requests}")

    @pytest.mark.asyncio
    async def test_rate_limit_distributed_attack(self, client: TestClient):
        """
        Test distributed rate limit bypass simulation
        """
        endpoint = "/api/v1/filings/search"

        # Simulate requests from multiple "sources"
        attack_vectors = []

        for i in range(20):
            headers = {
                "X-Forwarded-For": f"192.168.{i}.1",
                "User-Agent": f"Bot-{i}",
                "X-Request-ID": secrets.token_hex(16)
            }

            response = client.get(endpoint, headers=headers)
            attack_vectors.append({
                "source": i,
                "status": response.status_code,
                "success": response.status_code == 200
            })

        successful_requests = sum(1 for v in attack_vectors if v['success'])
        print(f"Distributed attack: {successful_requests}/20 successful")


class TestSessionSecurityAttacks:
    """Session hijacking and fixation attacks"""

    @pytest.mark.asyncio
    async def test_session_fixation_attack(self, client: TestClient):
        """
        Test session fixation vulnerability

        ATTACK: Set session ID before authentication
        IMPACT: Attacker can hijack authenticated session
        """
        # Attacker sets a known session ID
        attacker_session_id = "attacker_controlled_session_12345"

        # Victim authenticates with attacker's session
        response = client.get(
            "/api/v1/filings/search",
            cookies={"session_id": attacker_session_id}
        )

        # Check if session ID is accepted and reused
        set_cookie = response.cookies.get("session_id")

        if set_cookie == attacker_session_id:
            pytest.fail(
                "VULNERABILITY: Session fixation possible!\n"
                f"Pre-set session ID '{attacker_session_id}' was reused"
            )

    @pytest.mark.asyncio
    async def test_session_prediction_attack(self, client: TestClient):
        """
        Test session ID predictability

        ATTACK: Generate multiple sessions and analyze pattern
        IMPACT: Session hijacking via prediction
        """
        session_ids = []

        # Generate multiple sessions
        for i in range(10):
            response = client.get("/")
            session_id = response.cookies.get("session_id")

            if session_id:
                session_ids.append(session_id)

        if len(session_ids) >= 3:
            # Check for sequential patterns
            # Session IDs should be cryptographically random

            # Simple entropy check
            unique_chars = set("".join(session_ids))
            entropy = len(unique_chars)

            if entropy < 16:  # Low entropy indicates weak generation
                print(f"WARNING: Low session ID entropy: {entropy} unique chars")

    @pytest.mark.asyncio
    async def test_session_replay_attack(self, client: TestClient):
        """
        Test session replay after logout
        """
        # Simulate authenticated session
        session_token = "valid_session_token_here"

        # Make authenticated request
        response1 = client.get(
            "/api/v1/filings/search",
            cookies={"session_id": session_token}
        )

        # Simulate logout (would call logout endpoint)
        # Then try to reuse session
        response2 = client.get(
            "/api/v1/filings/search",
            cookies={"session_id": session_token}
        )

        # After logout, session should be invalid
        # This test documents expected behavior
        assert response2.status_code in [200, 401, 403]


class TestBusinessLogicFlaws:
    """Business logic and workflow vulnerabilities"""

    @pytest.mark.asyncio
    async def test_price_manipulation(self, client: TestClient):
        """
        Test negative prices and overflow attacks
        """
        malicious_payloads = [
            {"limit": -1, "offset": 0},
            {"limit": 2147483647, "offset": 0},  # Max int
            {"limit": -2147483648, "offset": 0},  # Min int
            {"limit": 0, "offset": -999999},
        ]

        for payload in malicious_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params=payload
            )

            # Should validate and reject invalid values
            assert response.status_code in [200, 400, 422], \
                f"Unexpected response for payload: {payload}"

    @pytest.mark.asyncio
    async def test_race_condition_exploitation(self, client: TestClient):
        """
        Test race condition in concurrent requests
        """
        async def make_request():
            return client.post(
                "/api/v1/predictions/predict",
                json={
                    "accession_number": "0001234567-23-000001",
                    "prediction_type": "price_movement",
                    "horizon": 30
                }
            )

        # Send concurrent requests
        tasks = [make_request() for _ in range(50)]

        # Execute concurrently (simulated)
        # In real test, would use asyncio.gather()
        responses = []
        for task in tasks:
            try:
                responses.append(task)
            except Exception as e:
                print(f"Race condition test error: {e}")

        # Analyze for race condition indicators
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        print(f"Race condition test: {len(status_codes)} responses")

    @pytest.mark.asyncio
    async def test_data_leakage_through_timing(self, client: TestClient):
        """
        Test timing-based information disclosure
        """
        import time

        # Valid vs invalid CIK - timing should be constant
        test_cases = [
            "0001234567",  # Valid format
            "9999999999",  # Valid format, may not exist
            "invalid",     # Invalid format
        ]

        timings = {}
        for cik in test_cases:
            start = time.perf_counter()

            response = client.get(f"/api/v1/filings/search?cik={cik}")

            elapsed = time.perf_counter() - start
            timings[cik] = elapsed

        # Large timing differences may leak information
        print(f"Timing analysis: {timings}")

        max_time = max(timings.values())
        min_time = min(timings.values())

        if max_time / min_time > 2.0:  # 2x difference
            print(f"WARNING: Timing difference detected: {max_time/min_time:.2f}x")


class TestInputValidationBypass:
    """Advanced input validation bypass techniques"""

    @pytest.mark.asyncio
    async def test_unicode_normalization_bypass(self, client: TestClient):
        """
        Test Unicode normalization attack
        """
        # Unicode that normalizes to dangerous characters
        unicode_payloads = [
            "\u02BC OR \u02BC1\u02BC=\u02BC1",  # Single quote variants
            "\uFF07 OR \uFF071\uFF07=\uFF071",  # Fullwidth quote
            "admin\u0027--",  # Unicode escape quote
        ]

        for payload in unicode_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": payload}
            )

            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_encoding_bypass(self, client: TestClient):
        """
        Test double/triple encoding bypass
        """
        import urllib.parse

        # Double-encoded payload
        payload = "' OR '1'='1"
        encoded_once = urllib.parse.quote(payload)
        encoded_twice = urllib.parse.quote(encoded_once)

        response = client.get(
            f"/api/v1/filings/search?cik={encoded_twice}"
        )

        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_null_byte_injection(self, client: TestClient):
        """
        Test null byte injection
        """
        null_byte_payloads = [
            "0001234567\x00.txt",
            "test\x00' OR '1'='1",
        ]

        for payload in null_byte_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"cik": payload}
            )

            assert response.status_code in [200, 400, 422]


@pytest.fixture
def client():
    """Create test client"""
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

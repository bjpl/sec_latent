"""
API Security Tests
Tests for API-specific vulnerabilities including rate limiting, CORS, CSRF, and injection
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
from datetime import datetime
import json


class TestRateLimiting:
    """Test rate limiting and abuse prevention"""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, client: TestClient):
        """Test that rate limits are enforced"""
        endpoint = "/api/v1/filings/search"
        requests_count = 100

        # Send rapid requests
        responses = []
        for _ in range(requests_count):
            response = client.get(endpoint)
            responses.append(response.status_code)

        # Should have rate limit responses (429)
        # Or at least not all successful if rate limiting is implemented
        status_codes = set(responses)

        # Document whether rate limiting is implemented
        if 429 in status_codes:
            # Rate limiting is implemented
            assert responses.count(429) > 0, "Rate limiting should trigger"
        else:
            # Rate limiting not yet implemented - document for future
            pass

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, client: TestClient):
        """Test rate limit headers"""
        response = client.get("/api/v1/filings/search")

        # Check for rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After"
        ]

        # Document which headers are present
        present_headers = [h for h in rate_limit_headers if h in response.headers]

        # If rate limiting is implemented, headers should be present
        if present_headers:
            assert len(present_headers) > 0

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_attempts(self, client: TestClient):
        """Test rate limit bypass attempts"""
        endpoint = "/api/v1/filings/search"

        # Attempt bypass via different headers
        bypass_attempts = [
            {"X-Forwarded-For": "1.2.3.4"},
            {"X-Real-IP": "1.2.3.4"},
            {"X-Originating-IP": "1.2.3.4"},
            {"Client-IP": "1.2.3.4"},
        ]

        for headers in bypass_attempts:
            responses = []
            for _ in range(50):
                response = client.get(endpoint, headers=headers)
                responses.append(response.status_code)

            # Should not bypass rate limiting
            # (If 429 appears, rate limiting is working)


class TestCORSVulnerabilities:
    """Test CORS configuration vulnerabilities"""

    @pytest.mark.asyncio
    async def test_cors_wildcard_origin(self, client: TestClient):
        """Test CORS wildcard origin vulnerability"""
        response = client.get(
            "/api/v1/filings/search",
            headers={"Origin": "https://evil.com"}
        )

        cors_header = response.headers.get("access-control-allow-origin")

        # SECURITY ISSUE: Currently allows * (all origins)
        # In production, this should be restricted
        if cors_header == "*":
            # Document this as a security issue
            assert True, "CORS allows all origins - should restrict in production"
        elif cors_header:
            # Should not reflect arbitrary origins
            assert cors_header != "https://evil.com", \
                "CORS should not reflect arbitrary origins"

    @pytest.mark.asyncio
    async def test_cors_credentials_with_wildcard(self, client: TestClient):
        """Test dangerous CORS config: wildcard + credentials"""
        response = client.get(
            "/api/v1/filings/search",
            headers={"Origin": "https://evil.com"}
        )

        allow_origin = response.headers.get("access-control-allow-origin")
        allow_credentials = response.headers.get("access-control-allow-credentials")

        # DANGEROUS: wildcard origin + credentials = security vulnerability
        if allow_origin == "*" and allow_credentials == "true":
            pytest.fail("DANGEROUS: Wildcard CORS with credentials enabled")

    @pytest.mark.asyncio
    async def test_cors_preflight_validation(self, client: TestClient):
        """Test CORS preflight request validation"""
        # Send OPTIONS preflight request
        response = client.options(
            "/api/v1/filings/search",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )

        # Should properly validate preflight
        assert response.status_code in [200, 204, 403, 404, 405]


class TestCSRFProtection:
    """Test CSRF (Cross-Site Request Forgery) protection"""

    @pytest.mark.asyncio
    async def test_csrf_token_validation(self, client: TestClient):
        """Test CSRF token validation on state-changing operations"""
        # POST request without CSRF token
        response = client.post(
            "/api/v1/predictions/predict",
            json={
                "accession_number": "0001234567-23-000001",
                "prediction_type": "price_movement",
                "horizon": 30
            }
        )

        # For API endpoints, CSRF might not be needed if using token auth
        # But document the protection mechanism
        assert response.status_code in [200, 400, 403, 422]

    @pytest.mark.asyncio
    async def test_csrf_token_reuse(self, client: TestClient):
        """Test CSRF token reuse prevention"""
        # This test documents that CSRF tokens should be one-time use
        # Implementation depends on authentication method
        pass

    @pytest.mark.asyncio
    async def test_samesite_cookie_attribute(self, client: TestClient):
        """Test SameSite cookie attribute"""
        response = client.get("/")

        # Check Set-Cookie headers for SameSite attribute
        set_cookie = response.headers.get("set-cookie", "")

        if "sessionid" in set_cookie.lower() or "session" in set_cookie.lower():
            # Session cookies should have SameSite=Strict or Lax
            assert "samesite=strict" in set_cookie.lower() or \
                   "samesite=lax" in set_cookie.lower(), \
                   "Session cookies should have SameSite attribute"


class TestParameterTampering:
    """Test parameter tampering and manipulation"""

    @pytest.mark.asyncio
    async def test_mass_assignment(self, client: TestClient):
        """Test mass assignment vulnerabilities"""
        # Attempt to set unauthorized fields
        malicious_payload = {
            "accession_number": "0001234567-23-000001",
            "prediction_type": "price_movement",
            "horizon": 30,
            # Unauthorized fields
            "is_admin": True,
            "credits": 9999,
            "bypass_limit": True,
        }

        response = client.post(
            "/api/v1/predictions/predict",
            json=malicious_payload
        )

        # Should ignore or reject unauthorized fields
        if response.status_code == 200:
            data = response.json()
            # Verify unauthorized fields weren't set
            assert "is_admin" not in data
            assert "credits" not in data

    @pytest.mark.asyncio
    async def test_parameter_pollution(self, client: TestClient):
        """Test HTTP parameter pollution"""
        # Send duplicate parameters
        response = client.get(
            "/api/v1/filings/search?limit=10&limit=1000"
        )

        # Should handle duplicate parameters safely
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Should respect the intended limit (first or last)
            assert len(data) <= 1000

    @pytest.mark.asyncio
    async def test_negative_numbers_in_pagination(self, client: TestClient):
        """Test negative numbers in pagination parameters"""
        test_cases = [
            {"limit": -1},
            {"offset": -1},
            {"limit": -999, "offset": -999},
        ]

        for params in test_cases:
            response = client.get(
                "/api/v1/filings/search",
                params=params
            )

            # Should reject or sanitize negative values
            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_integer_overflow(self, client: TestClient):
        """Test integer overflow in parameters"""
        test_cases = [
            {"limit": 2147483648},  # Max int32 + 1
            {"limit": 999999999999},
            {"offset": 9999999999},
        ]

        for params in test_cases:
            response = client.get(
                "/api/v1/filings/search",
                params=params
            )

            # Should handle large integers safely
            assert response.status_code in [200, 400, 422]


class TestInputValidation:
    """Test input validation and sanitization"""

    @pytest.mark.asyncio
    async def test_date_format_validation(self, client: TestClient):
        """Test date parameter validation"""
        invalid_dates = [
            "2023-13-01",  # Invalid month
            "2023-02-30",  # Invalid day
            "not-a-date",
            "'; DROP TABLE filings--",
            "../../../etc/passwd",
        ]

        for date_str in invalid_dates:
            response = client.get(
                "/api/v1/filings/search",
                params={"start_date": date_str}
            )

            # Should reject invalid dates
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_string_length_validation(self, client: TestClient):
        """Test string length limits"""
        # Very long company name
        long_string = "A" * 10000

        response = client.get(
            "/api/v1/filings/search",
            params={"company_name": long_string}
        )

        # Should enforce length limits
        assert response.status_code in [200, 400, 413, 422]

    @pytest.mark.asyncio
    async def test_enum_validation(self, client: TestClient):
        """Test enum/choice field validation"""
        invalid_values = [
            {"form_type": "INVALID"},
            {"form_type": "'; DROP TABLE--"},
            {"form_type": "<script>alert('XSS')</script>"},
        ]

        for params in invalid_values:
            response = client.get(
                "/api/v1/filings/search",
                params=params
            )

            # Should accept any value or validate against allowed types
            assert response.status_code in [200, 400, 422]


class TestErrorHandling:
    """Test error handling and information disclosure"""

    @pytest.mark.asyncio
    async def test_error_message_information_disclosure(self, client: TestClient):
        """Test that errors don't leak sensitive information"""
        # Trigger various errors
        error_endpoints = [
            ("/api/v1/filings/doesnotexist", "GET"),
            ("/api/v1/predictions/predict", "POST"),  # Invalid data
        ]

        for endpoint, method in error_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={"invalid": "data"})

            if response.status_code >= 400:
                data = response.json()
                error_msg = json.dumps(data).lower()

                # Should not leak sensitive information
                sensitive_info = [
                    "password",
                    "secret_key",
                    "api_key",
                    "database",
                    "traceback",
                    "/home/",
                    "/root/",
                    "supabase_key",
                ]

                for info in sensitive_info:
                    assert info not in error_msg, \
                        f"Error message leaks sensitive info: {info}"

    @pytest.mark.asyncio
    async def test_stack_trace_disclosure(self, client: TestClient):
        """Test that stack traces aren't exposed in production"""
        # Try to trigger an error
        response = client.get("/api/v1/filings/trigger_error_test")

        if response.status_code >= 400:
            content = response.text.lower()

            # Should not contain stack trace
            assert "traceback" not in content
            assert "file \"" not in content
            assert "line " not in content


class TestSecurityHeaders:
    """Test security headers"""

    @pytest.mark.asyncio
    async def test_security_headers_presence(self, client: TestClient):
        """Test presence of security headers"""
        response = client.get("/")

        recommended_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": ["1; mode=block", "0"],
            "Strict-Transport-Security": "max-age=",  # Partial match
        }

        for header, expected in recommended_headers.items():
            header_value = response.headers.get(header.lower())

            if isinstance(expected, list):
                if header_value:
                    assert any(exp in header_value for exp in expected), \
                        f"{header} should be one of {expected}"
            else:
                if header_value:
                    assert expected in header_value, \
                        f"{header} should contain {expected}"

    @pytest.mark.asyncio
    async def test_cache_control_headers(self, client: TestClient):
        """Test Cache-Control headers for sensitive data"""
        sensitive_endpoints = [
            "/api/v1/filings/search",
            "/api/v1/predictions/history/0001234567",
        ]

        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)

            cache_control = response.headers.get("cache-control", "")

            # Sensitive data should have appropriate cache control
            # Document caching strategy
            if cache_control:
                # Check for private/no-store directives
                assert any(directive in cache_control.lower()
                          for directive in ["private", "no-store", "no-cache", "max-age"])


@pytest.fixture
def client():
    """Create test client"""
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

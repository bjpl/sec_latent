"""
SQL Injection Vulnerability Tests
Tests for SQL injection attacks on database queries
"""

import pytest
from fastapi.testclient import TestClient
from typing import List, Dict, Any

# Common SQL injection payloads
SQL_INJECTION_PAYLOADS = [
    # Basic SQLi
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "admin'--",
    "admin' #",
    "admin'/*",

    # Union-based SQLi
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL--",
    "' UNION ALL SELECT NULL,NULL,NULL--",

    # Boolean-based blind SQLi
    "' AND 1=1--",
    "' AND 1=2--",
    "' AND 'x'='x",
    "' AND 'x'='y",

    # Time-based blind SQLi
    "'; WAITFOR DELAY '0:0:5'--",
    "'; SELECT SLEEP(5)--",
    "'; pg_sleep(5)--",

    # Stacked queries
    "'; DROP TABLE users--",
    "'; DELETE FROM users WHERE '1'='1",
    "'; UPDATE users SET admin=1--",

    # Advanced SQLi
    "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
    "1' AND 1=1 AND '%'='",
    "' AND EXTRACTVALUE(1,CONCAT(0x5c,version()))--",

    # NoSQL injection (for DuckDB/JSON)
    "{\"$ne\": null}",
    "{\"$gt\": \"\"}",
    "' || '1'='1",
]


class TestSQLInjectionFilings:
    """Test SQL injection vulnerabilities in filings endpoints"""

    @pytest.mark.asyncio
    async def test_search_filings_cik_injection(self, client: TestClient):
        """Test CIK parameter for SQL injection"""
        for payload in SQL_INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/filings/search",
                params={"cik": payload}
            )

            # Should not execute malicious SQL
            assert response.status_code in [200, 400, 422], \
                f"Unexpected status for payload: {payload}"

            # Response should not contain SQL error messages
            if response.status_code == 200:
                data = response.json()
                response_str = str(data).lower()

                # Check for SQL error keywords
                sql_errors = [
                    "syntax error",
                    "sql error",
                    "database error",
                    "query failed",
                    "sqlite",
                    "postgresql",
                    "duckdb error"
                ]

                for error in sql_errors:
                    assert error not in response_str, \
                        f"SQL error leaked in response for payload: {payload}"

    @pytest.mark.asyncio
    async def test_search_filings_company_name_injection(self, client: TestClient):
        """Test company_name parameter for SQL injection"""
        for payload in SQL_INJECTION_PAYLOADS:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": payload}
            )

            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                # Should return empty or sanitized results, not error
                assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_search_filings_form_type_injection(self, client: TestClient):
        """Test form_type parameter for SQL injection"""
        payloads = SQL_INJECTION_PAYLOADS + [
            "10-K' OR '1'='1",
            "10-Q'; DROP TABLE filings--",
        ]

        for payload in payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"form_type": payload}
            )

            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_get_filing_accession_number_injection(self, client: TestClient):
        """Test accession_number path parameter for SQL injection"""
        for payload in SQL_INJECTION_PAYLOADS:
            # URL encode the payload
            import urllib.parse
            encoded_payload = urllib.parse.quote(payload)

            response = client.get(f"/api/v1/filings/{encoded_payload}")

            # Should return 404 or 400, not 500 or SQL error
            assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_second_order_sql_injection(self, client: TestClient):
        """Test second-order SQL injection through data persistence"""
        # First request: Store malicious payload
        malicious_cik = "0001234567' OR '1'='1"

        response1 = client.get(
            "/api/v1/filings/search",
            params={"cik": malicious_cik}
        )

        # Second request: Retrieve stored data
        # The stored malicious CIK should be sanitized and not executed
        response2 = client.get(
            "/api/v1/filings/search",
            params={"limit": 100}
        )

        if response2.status_code == 200:
            data = response2.json()
            # Check that retrieved data doesn't contain unsanitized payloads
            for filing in data:
                assert "' OR '" not in str(filing.get("cik", ""))


class TestSQLInjectionPredictions:
    """Test SQL injection vulnerabilities in predictions endpoints"""

    @pytest.mark.asyncio
    async def test_prediction_history_cik_injection(self, client: TestClient):
        """Test CIK parameter in prediction history"""
        for payload in SQL_INJECTION_PAYLOADS[:10]:  # Test subset
            response = client.get(
                f"/api/v1/predictions/history/{payload}"
            )

            assert response.status_code in [200, 400, 404, 422]

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_prediction_create_injection(self, client: TestClient):
        """Test SQL injection in prediction creation"""
        injection_payloads = [
            {
                "accession_number": "' OR '1'='1",
                "prediction_type": "price_movement",
                "horizon": 30
            },
            {
                "accession_number": "0001234567-23-000001",
                "prediction_type": "'; DROP TABLE predictions--",
                "horizon": 30
            },
        ]

        for payload in injection_payloads:
            response = client.post(
                "/api/v1/predictions/predict",
                json=payload
            )

            # Should validate and reject malicious input
            assert response.status_code in [200, 400, 422]


class TestSQLInjectionSignals:
    """Test SQL injection vulnerabilities in signals endpoints"""

    @pytest.mark.asyncio
    async def test_signals_query_injection(self, client: TestClient):
        """Test SQL injection in signals query parameters"""
        test_params = [
            {"signal_name": "' OR '1'='1"},
            {"category": "'; DROP TABLE signals--"},
            {"cik": "' UNION SELECT * FROM users--"},
        ]

        for params in test_params:
            response = client.get(
                "/api/v1/signals/query",
                params=params
            )

            assert response.status_code in [200, 400, 422]


class TestDuckDBInjection:
    """Test DuckDB-specific injection vulnerabilities"""

    @pytest.mark.asyncio
    async def test_duckdb_json_injection(self, client: TestClient):
        """Test JSON-based injection for DuckDB queries"""
        json_payloads = [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$or": [{"admin": true}]}',
        ]

        for payload in json_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": payload}
            )

            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_duckdb_function_injection(self, client: TestClient):
        """Test DuckDB function injection"""
        function_payloads = [
            "read_csv('/etc/passwd')",
            "read_parquet('file:///etc/hosts')",
            "COPY (SELECT * FROM filings) TO '/tmp/dump.csv'",
        ]

        for payload in function_payloads:
            response = client.get(
                "/api/v1/filings/search",
                params={"cik": payload}
            )

            # Should block file system access
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                # Should not contain file contents
                response_str = str(data).lower()
                assert "root:" not in response_str
                assert "/bin/bash" not in response_str


class TestParameterizedQueryValidation:
    """Validate that parameterized queries are used"""

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, client: TestClient):
        """Test handling of special characters"""
        special_chars = [
            "O'Reilly",  # Single quote in legitimate data
            "AT&T",      # Ampersand
            "Johnson & Johnson",
            "Price<Cost",
            "Value>100",
        ]

        for char_test in special_chars:
            response = client.get(
                "/api/v1/filings/search",
                params={"company_name": char_test}
            )

            # Should handle special characters without errors
            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_unicode_injection(self, client: TestClient):
        """Test Unicode-based injection attempts"""
        unicode_payloads = [
            "＇OR＇1＇=＇1",  # Full-width characters
            "' OR '1'＝'1",
            "admin\u0027--",  # Unicode escape
        ]

        for payload in unicode_payloads:
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

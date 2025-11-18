"""
API Response Fixtures
Mock API responses for testing
"""
from typing import Dict, Any, List


def mock_api_response(status_code: int = 200, data: Any = None, message: str = "Success"):
    """Generate mock API response"""
    return {
        "status_code": status_code,
        "data": data,
        "message": message,
        "timestamp": "2024-10-18T00:00:00Z"
    }


def mock_filing_response(cik: str = "0000789019") -> Dict[str, Any]:
    """Mock filing API response"""
    return {
        "filing_id": f"filing-{cik}-001",
        "cik": cik,
        "company_name": "Test Corporation",
        "form_type": "10-K",
        "filing_date": "2024-07-31",
        "status": "processed",
        "signal_count": 150,
        "processing_time_ms": 1250
    }


def mock_signal_response(signal_count: int = 150) -> Dict[str, Any]:
    """Mock signal extraction response"""
    return {
        "filing_id": "test-filing-123",
        "signals": {
            "financial": [
                {"name": f"financial_signal_{i}", "value": 0.75, "confidence": 0.9}
                for i in range(50)
            ],
            "sentiment": [
                {"name": f"sentiment_signal_{i}", "value": 0.65, "confidence": 0.85}
                for i in range(30)
            ],
            "risk": [
                {"name": f"risk_signal_{i}", "value": 0.55, "confidence": 0.88}
                for i in range(40)
            ],
            "management": [
                {"name": f"management_signal_{i}", "value": 0.70, "confidence": 0.87}
                for i in range(30)
            ]
        },
        "total_signals": signal_count,
        "extraction_time_ms": 850
    }


def mock_prediction_response() -> Dict[str, Any]:
    """Mock prediction API response"""
    return {
        "prediction_id": "pred-123",
        "filing_id": "filing-123",
        "prediction": {
            "price_direction": "up",
            "confidence": 0.78,
            "magnitude": 0.05,
            "time_horizon": "1_month"
        },
        "model_used": "claude-3-5-sonnet-20241022",
        "signals_analyzed": 150,
        "processing_time_ms": 2400
    }


def mock_validation_response(passed: bool = True) -> Dict[str, Any]:
    """Mock FACT validation response"""
    return {
        "validation_id": "val-123",
        "overall_passed": passed,
        "confidence_score": 0.92 if passed else 0.65,
        "results": [
            {
                "type": "mathematical",
                "passed": passed,
                "confidence": 0.95,
                "severity": "low"
            },
            {
                "type": "logical",
                "passed": passed,
                "confidence": 0.90,
                "severity": "low"
            },
            {
                "type": "critical",
                "passed": passed,
                "confidence": 0.88,
                "severity": "medium"
            }
        ],
        "risk_level": "low" if passed else "high",
        "recommendations": ["All validations passed"] if passed else ["Review findings"]
    }


def mock_websocket_message(event_type: str = "signal_update") -> Dict[str, Any]:
    """Mock WebSocket message"""
    return {
        "type": event_type,
        "data": {
            "filing_id": "filing-123",
            "status": "processing",
            "progress": 0.45,
            "signals_extracted": 68
        },
        "timestamp": "2024-10-18T00:00:00Z"
    }


# Error response fixtures

def mock_error_response(status_code: int = 400, error: str = "Bad Request") -> Dict[str, Any]:
    """Mock error response"""
    return {
        "status_code": status_code,
        "error": error,
        "detail": f"Test error: {error}",
        "timestamp": "2024-10-18T00:00:00Z"
    }


def mock_rate_limit_response() -> Dict[str, Any]:
    """Mock rate limit error"""
    return {
        "status_code": 429,
        "error": "Rate Limit Exceeded",
        "detail": "Too many requests. Please retry after 60 seconds.",
        "retry_after": 60,
        "timestamp": "2024-10-18T00:00:00Z"
    }


def mock_validation_error() -> Dict[str, Any]:
    """Mock validation error"""
    return {
        "status_code": 422,
        "error": "Validation Error",
        "detail": [
            {
                "loc": ["body", "cik"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ],
        "timestamp": "2024-10-18T00:00:00Z"
    }

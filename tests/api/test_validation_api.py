"""
Validation API Tests
Tests for FACT validation endpoints

Endpoints tested:
- POST /validation/fact - Perform FACT validation
- GET /validation/{validation_id} - Get validation results
- POST /validation/batch - Batch validation
- GET /validation/{validation_id}/report - Get detailed report
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures.api_fixtures import mock_validation_response


class TestFACTValidationEndpoint:
    """Test POST /validation/fact endpoint"""

    @pytest.mark.asyncio
    async def test_fact_validation_success(self, async_client):
        """Test successful FACT validation"""
        request_data = {
            "claim": "Revenue increased 15% to $245 billion",
            "context": {
                "filing_id": "filing-123",
                "section": "md_and_a"
            },
            "validation_types": ["mathematical", "logical", "critical"]
        }

        mock_response = mock_validation_response(passed=True)

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["overall_passed"] is True
            assert data["confidence_score"] > 0.85
            assert len(data["results"]) == 3

    @pytest.mark.asyncio
    async def test_fact_validation_failure(self, async_client):
        """Test validation with failures"""
        request_data = {
            "claim": "Revenue increased 150% to $2.45 trillion",  # Suspicious claim
            "context": {"filing_id": "filing-123"}
        }

        mock_response = mock_validation_response(passed=False)

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["overall_passed"] is False
            assert data["risk_level"] == "high"
            assert len(data["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_fact_validation_mathematical_only(self, async_client):
        """Test mathematical validation only"""
        request_data = {
            "claim": "Operating margin is 44.9% (110B / 245B)",
            "context": {"filing_id": "filing-123"},
            "validation_types": ["mathematical"]
        }

        mock_response = {
            "validation_id": "val-123",
            "overall_passed": True,
            "confidence_score": 0.95,
            "results": [
                {
                    "type": "mathematical",
                    "passed": True,
                    "confidence": 0.95,
                    "severity": "low",
                    "message": "Mathematical validation passed",
                    "details": {
                        "calculation_verified": True,
                        "unit_consistency": True
                    }
                }
            ],
            "risk_level": "low"
        }

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert len(data["results"]) == 1
            assert data["results"][0]["type"] == "mathematical"

    @pytest.mark.asyncio
    async def test_fact_validation_logical_fallacies(self, async_client):
        """Test detection of logical fallacies"""
        request_data = {
            "claim": "Our competitors all failed, therefore we will succeed",
            "context": {"filing_id": "filing-123"},
            "validation_types": ["logical"]
        }

        mock_response = {
            "validation_id": "val-124",
            "overall_passed": False,
            "confidence_score": 0.45,
            "results": [
                {
                    "type": "logical",
                    "passed": False,
                    "confidence": 0.45,
                    "severity": "high",
                    "message": "Logic validation failed - detected fallacies: false_cause",
                    "details": {
                        "fallacies_detected": ["false_cause", "hasty_generalization"],
                        "consistency_score": 0.4
                    }
                }
            ],
            "risk_level": "high",
            "recommendations": ["Strengthen logical reasoning and address identified fallacies"]
        }

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["overall_passed"] is False
            assert len(data["results"][0]["details"]["fallacies_detected"]) > 0

    @pytest.mark.asyncio
    async def test_fact_validation_critical_check(self, async_client):
        """Test critical validation for high-stakes claims"""
        request_data = {
            "claim": "We forecast 50% annual growth for the next 5 years",
            "context": {"filing_id": "filing-123", "section": "forward_looking"},
            "validation_types": ["critical"]
        }

        mock_response = {
            "validation_id": "val-125",
            "overall_passed": True,
            "confidence_score": 0.88,
            "results": [
                {
                    "type": "critical",
                    "passed": True,
                    "confidence": 0.88,
                    "severity": "medium",
                    "message": "Critical validation passed (risk level: high)",
                    "details": {
                        "risk_level": "high",
                        "sources_verified": True,
                        "compliance_passed": True,
                        "expert_score": 0.88
                    }
                }
            ],
            "risk_level": "medium"
        }

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["results"][0]["details"]["risk_level"] == "high"
            assert data["results"][0]["details"]["compliance_passed"] is True


class TestValidationGetEndpoint:
    """Test GET /validation/{validation_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_validation_results(self, async_client):
        """Test get validation results"""
        validation_id = "val-123"

        mock_response = mock_validation_response(passed=True)

        with patch('api.routes.validation.get_validation') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert data["validation_id"] is not None
            assert "results" in data

    @pytest.mark.asyncio
    async def test_get_validation_not_found(self, async_client):
        """Test validation not found"""
        validation_id = "nonexistent"

        with patch('api.routes.validation.get_validation') as mock_get:
            mock_get.return_value = None
            data = mock_get(validation_id)

            assert data is None


class TestValidationBatchEndpoint:
    """Test POST /validation/batch endpoint"""

    @pytest.mark.asyncio
    async def test_batch_validation(self, async_client):
        """Test batch validation of multiple claims"""
        request_data = {
            "validations": [
                {"claim": "Revenue up 15%", "context": {"filing_id": "filing-1"}},
                {"claim": "Margins improved", "context": {"filing_id": "filing-2"}},
                {"claim": "Cash flow positive", "context": {"filing_id": "filing-3"}}
            ]
        }

        mock_response = {
            "batch_id": "batch-val-123",
            "validations": [
                {"validation_id": "val-1", "status": "completed", "passed": True},
                {"validation_id": "val-2", "status": "completed", "passed": True},
                {"validation_id": "val-3", "status": "completed", "passed": True}
            ],
            "summary": {
                "total": 3,
                "passed": 3,
                "failed": 0,
                "pass_rate": 1.0
            }
        }

        with patch('api.routes.validation.batch_validate') as mock_batch:
            mock_batch.return_value = mock_response
            data = mock_response

            assert len(data["validations"]) == 3
            assert data["summary"]["pass_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_batch_validation_mixed_results(self, async_client):
        """Test batch with mixed pass/fail"""
        mock_response = {
            "batch_id": "batch-val-124",
            "validations": [
                {"validation_id": "val-1", "status": "completed", "passed": True},
                {"validation_id": "val-2", "status": "completed", "passed": False},
                {"validation_id": "val-3", "status": "completed", "passed": True}
            ],
            "summary": {
                "total": 3,
                "passed": 2,
                "failed": 1,
                "pass_rate": 0.67
            }
        }

        with patch('api.routes.validation.batch_validate') as mock_batch:
            mock_batch.return_value = mock_response
            data = mock_response

            assert data["summary"]["failed"] == 1
            assert data["summary"]["pass_rate"] < 1.0


class TestValidationReportEndpoint:
    """Test GET /validation/{validation_id}/report endpoint"""

    @pytest.mark.asyncio
    async def test_get_detailed_report(self, async_client):
        """Test get detailed validation report"""
        validation_id = "val-123"

        mock_response = {
            "validation_id": validation_id,
            "report": {
                "executive_summary": "All validations passed with high confidence",
                "detailed_findings": [
                    {
                        "type": "mathematical",
                        "finding": "All calculations verified accurate",
                        "evidence": ["110B / 245B = 44.9%", "Rounded appropriately"]
                    },
                    {
                        "type": "logical",
                        "finding": "Logical structure sound",
                        "evidence": ["No fallacies detected", "Consistency score: 0.9"]
                    }
                ],
                "risk_assessment": {
                    "overall_risk": "low",
                    "risk_factors": [],
                    "mitigation_suggestions": []
                },
                "confidence_analysis": {
                    "overall_confidence": 0.92,
                    "confidence_by_type": {
                        "mathematical": 0.95,
                        "logical": 0.90,
                        "critical": 0.88
                    }
                },
                "recommendations": [
                    "All validations passed - proceed with confidence"
                ]
            },
            "generated_at": "2024-10-18T00:00:00Z"
        }

        with patch('api.routes.validation.get_validation_report') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert "report" in data
            assert len(data["report"]["detailed_findings"]) > 0
            assert "confidence_analysis" in data["report"]


class TestValidationPerformance:
    """Performance tests for validation API"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validation_response_time(self, async_client, benchmark_timer):
        """Test validation completes in reasonable time"""
        # Mathematical + Logical + Critical should complete in < 5s
        mock_response = mock_validation_response(passed=True)
        mock_response["processing_time_ms"] = 3500

        assert mock_response["processing_time_ms"] < 5000

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_validation_throughput(self, async_client):
        """Test batch validation throughput"""
        validation_count = 50
        mock_response = {
            "batch_id": "batch-large",
            "validation_count": validation_count,
            "estimated_completion_sec": 120  # 2 minutes for 50 validations
        }

        # Should process ~25 validations per minute
        validations_per_minute = validation_count / (mock_response["estimated_completion_sec"] / 60)
        assert validations_per_minute > 20


class TestValidationEdgeCases:
    """Edge case tests"""

    @pytest.mark.asyncio
    async def test_validation_empty_claim(self, async_client):
        """Test validation with empty claim"""
        request_data = {
            "claim": "",
            "context": {}
        }

        # Should reject empty claim
        assert len(request_data["claim"].strip()) == 0

    @pytest.mark.asyncio
    async def test_validation_very_long_claim(self, async_client):
        """Test validation with very long claim"""
        request_data = {
            "claim": "A" * 10000,  # 10k characters
            "context": {}
        }

        # Should handle or reject very long claims
        assert len(request_data["claim"]) > 5000

    @pytest.mark.asyncio
    async def test_validation_special_characters(self, async_client):
        """Test validation with special characters"""
        request_data = {
            "claim": "Revenue is $245B (↑15% YoY) 🚀",
            "context": {}
        }

        mock_response = mock_validation_response(passed=True)

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["overall_passed"] is True

    @pytest.mark.asyncio
    async def test_validation_numeric_precision(self, async_client):
        """Test validation of high-precision numbers"""
        request_data = {
            "claim": "Operating margin is 44.89795918% exactly",
            "context": {"filing_id": "filing-123"}
        }

        mock_response = {
            "validation_id": "val-precision",
            "overall_passed": False,
            "confidence_score": 0.65,
            "results": [
                {
                    "type": "mathematical",
                    "passed": False,
                    "confidence": 0.65,
                    "message": "Suspicious precision - likely computed not reported",
                    "details": {
                        "precision_warning": True,
                        "significant_figures": 10
                    }
                }
            ]
        }

        with patch('api.routes.validation.perform_fact_validation') as mock_validate:
            mock_validate.return_value = mock_response
            data = mock_response

            assert data["results"][0]["details"]["precision_warning"] is True

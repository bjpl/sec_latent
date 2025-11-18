"""
Test fixtures and mock data for validation testing.
"""

from typing import Dict, List, Any


class ValidationTestFixtures:
    """Common test fixtures for validation tests."""

    @staticmethod
    def get_financial_claims() -> List[Dict[str, Any]]:
        """Get sample financial claims for testing."""
        return [
            {
                "claim": "Revenue increased by 25% from $100M to $125M",
                "context": {"year": 2024, "verified": True},
                "expected_valid": True,
                "risk_level": "low"
            },
            {
                "claim": "We forecast revenue growth of 50% next quarter",
                "context": {"forecast": True, "time_horizon": 90},
                "expected_valid": False,
                "risk_level": "high"
            },
            {
                "claim": "EBITDA margin improved from 15% to 18%",
                "context": {"verified": True},
                "expected_valid": True,
                "risk_level": "low"
            },
            {
                "claim": "Stock price will triple in 6 months",
                "context": {"prediction": True, "time_horizon": 180},
                "expected_valid": False,
                "risk_level": "critical"
            }
        ]

    @staticmethod
    def get_logical_claims() -> List[Dict[str, Any]]:
        """Get sample logical reasoning claims."""
        return [
            {
                "claim": "Since revenue increased and costs decreased, profit margin improved",
                "context": {},
                "expected_valid": True,
                "has_structure": True
            },
            {
                "claim": "Revenue increased therefore costs must have decreased",
                "context": {},
                "expected_valid": False,
                "has_structure": True,
                "fallacy": "non-sequitur"
            },
            {
                "claim": "Everyone says this stock will go up, so it will",
                "context": {},
                "expected_valid": False,
                "has_structure": False,
                "fallacy": "bandwagon"
            }
        ]

    @staticmethod
    def get_mathematical_claims() -> List[Dict[str, Any]]:
        """Get sample mathematical claims for testing."""
        return [
            {
                "claim": "10% of $100 equals $10",
                "context": {},
                "expected_valid": True,
                "numbers": [10, 100, 10]
            },
            {
                "claim": "Revenue grew 50% from $100M to $160M",
                "context": {},
                "expected_valid": False,  # Math is wrong (should be $150M)
                "numbers": [50, 100, 160]
            },
            {
                "claim": "Profit margin: $25M profit / $100M revenue = 25%",
                "context": {},
                "expected_valid": True,
                "numbers": [25, 100, 25]
            }
        ]

    @staticmethod
    def get_model_outputs_high_agreement() -> Dict[str, Dict[str, float]]:
        """Get model outputs with high agreement."""
        return {
            "model1": {"confidence": 0.90},
            "model2": {"confidence": 0.88},
            "model3": {"confidence": 0.92},
            "model4": {"confidence": 0.89}
        }

    @staticmethod
    def get_model_outputs_low_agreement() -> Dict[str, Dict[str, float]]:
        """Get model outputs with low agreement."""
        return {
            "model1": {"confidence": 0.95},
            "model2": {"confidence": 0.50},
            "model3": {"confidence": 0.70},
            "model4": {"confidence": 0.45}
        }

    @staticmethod
    def get_model_outputs_moderate_agreement() -> Dict[str, Dict[str, float]]:
        """Get model outputs with moderate agreement."""
        return {
            "model1": {"confidence": 0.80},
            "model2": {"confidence": 0.75},
            "model3": {"confidence": 0.85},
            "model4": {"confidence": 0.78}
        }

    @staticmethod
    def get_risk_contexts() -> Dict[str, Dict[str, Any]]:
        """Get various risk context scenarios."""
        return {
            "low_risk": {
                "historical_data": True,
                "verified": True,
                "data_quality": 0.95
            },
            "moderate_risk": {
                "forecast": True,
                "time_horizon": 90,
                "data_quality": 0.80
            },
            "high_risk": {
                "prediction": True,
                "time_horizon": 365,
                "uncertainty_high": True,
                "historical_volatility": 0.8
            },
            "critical_risk": {
                "prediction": True,
                "time_horizon": 730,
                "uncertainty_high": True,
                "historical_volatility": 0.95,
                "data_quality": 0.5,
                "sample_size": 10
            }
        }

    @staticmethod
    def get_edge_cases() -> List[Dict[str, Any]]:
        """Get edge case test scenarios."""
        return [
            {
                "name": "empty_claim",
                "claim": "",
                "context": {},
                "should_handle": True
            },
            {
                "name": "very_long_claim",
                "claim": "Revenue " * 1000 + "increased",
                "context": {},
                "should_handle": True
            },
            {
                "name": "special_characters",
                "claim": "Revenue: $100M (Q1) → $125M (Q2) ≈ 25% ↑",
                "context": {},
                "should_handle": True
            },
            {
                "name": "unicode",
                "claim": "Revenue: ¥100万, Profit: €50千",
                "context": {},
                "should_handle": True
            },
            {
                "name": "extreme_numbers",
                "claim": "Revenue: $999999999999999",
                "context": {},
                "should_handle": True
            },
            {
                "name": "contradictory",
                "claim": "Revenue increased but revenue decreased",
                "context": {},
                "should_handle": True,
                "expected_contradiction": True
            }
        ]

    @staticmethod
    def get_validation_metrics_samples() -> List[tuple]:
        """Get sample data for metrics calculation."""
        return [
            # (predictions, actuals, confidences, expected_accuracy)
            (
                [True, True, False, False],
                [True, True, False, False],
                [0.9, 0.9, 0.9, 0.9],
                1.0
            ),
            (
                [True, True, True, False, False],
                [True, False, True, False, True],
                [0.9, 0.8, 0.85, 0.9, 0.7],
                0.6
            ),
            (
                [True] * 10,
                [True] * 8 + [False] * 2,
                [0.8] * 10,
                0.8
            )
        ]


class MockModelInterface:
    """Mock interface for testing model integrations."""

    def __init__(self, base_confidence: float = 0.85):
        """Initialize mock model."""
        self.base_confidence = base_confidence
        self.call_count = 0

    def predict(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock prediction method."""
        self.call_count += 1
        return {
            "confidence": self.base_confidence,
            "result": "valid" if self.base_confidence > 0.7 else "invalid"
        }

    def reset(self):
        """Reset call counter."""
        self.call_count = 0


class ValidationScenarios:
    """Common validation test scenarios."""

    @staticmethod
    def get_sec_filing_scenarios() -> List[Dict[str, Any]]:
        """Get SEC filing analysis scenarios."""
        return [
            {
                "scenario": "earnings_forecast",
                "claim": "Q4 earnings projected at $2.50 per share",
                "context": {
                    "filing_type": "10-Q",
                    "forecast": True,
                    "time_horizon": 90
                },
                "expected_risk": "high",
                "expected_adjustment": 0.75
            },
            {
                "scenario": "historical_performance",
                "claim": "Revenue grew 15% annually over past 5 years",
                "context": {
                    "filing_type": "10-K",
                    "historical": True,
                    "verified": True
                },
                "expected_risk": "low",
                "expected_adjustment": 0.95
            },
            {
                "scenario": "risk_factor_disclosure",
                "claim": "Market risks may impact future performance",
                "context": {
                    "filing_type": "10-K",
                    "section": "risk_factors",
                    "regulatory": True
                },
                "expected_risk": "moderate",
                "expected_adjustment": 0.85
            }
        ]

    @staticmethod
    def get_stress_test_scenarios() -> List[Dict[str, Any]]:
        """Get stress test scenarios."""
        return [
            {
                "name": "high_volume",
                "claim_count": 1000,
                "timeout": 60,
                "max_failures": 10
            },
            {
                "name": "concurrent_validation",
                "concurrent_requests": 50,
                "timeout": 30,
                "max_failures": 5
            },
            {
                "name": "large_context",
                "context_size_mb": 10,
                "timeout": 20,
                "max_failures": 2
            }
        ]

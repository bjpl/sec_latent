"""
Comprehensive tests for FACT framework.

Tests cover:
- Mathematical verification
- Logic validation
- Critical external checks
- Edge cases and failure modes
"""

import unittest
from unittest.mock import Mock, patch
from src.validation.fact import (
    FACTValidator,
    ValidationType,
    ValidationSeverity,
    ValidationResult,
    ValidationReport
)


class TestFACTValidator(unittest.TestCase):
    """Test suite for FACT validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FACTValidator(
            confidence_threshold=0.85,
            enable_logging=False
        )

    def test_initialization(self):
        """Test validator initialization."""
        self.assertEqual(self.validator.math_model, "qwen2.5-coder")
        self.assertEqual(self.validator.logic_model, "deepseek-r1")
        self.assertEqual(self.validator.critical_model, "claude-3.5")
        self.assertEqual(self.validator.confidence_threshold, 0.85)

    def test_mathematical_validation_pass(self):
        """Test mathematical validation with correct calculations."""
        claim = "Revenue increased by 25% from $100M to $125M"
        context = {"year": 2024}

        result = self.validator._validate_mathematical(claim, context)

        self.assertEqual(result.validation_type, ValidationType.MATHEMATICAL)
        self.assertTrue(result.passed)
        self.assertGreater(result.confidence, 0.8)
        self.assertEqual(result.model_used, "qwen2.5-coder")

    def test_mathematical_validation_with_numbers(self):
        """Test extraction and validation of numerical claims."""
        claim = "The company reported $45.3 million in revenue with a 12.5% profit margin"
        context = {}

        result = self.validator._validate_mathematical(claim, context)

        self.assertIn('numbers_found', result.details)
        self.assertGreater(result.details['numbers_found'], 0)

    def test_logical_validation_pass(self):
        """Test logical validation with sound reasoning."""
        claim = "Since revenue increased and costs decreased, therefore profit margin improved"
        context = {}

        result = self.validator._validate_logical(claim, context)

        self.assertEqual(result.validation_type, ValidationType.LOGICAL)
        self.assertTrue(result.passed)
        self.assertIn('logical_structure', result.details)
        self.assertTrue(result.details['logical_structure'])

    def test_logical_validation_no_structure(self):
        """Test logical validation without clear structure."""
        claim = "The company is doing well"
        context = {}

        result = self.validator._validate_logical(claim, context)

        self.assertFalse(result.details['logical_structure'])

    def test_critical_validation_high_risk(self):
        """Test critical validation for high-risk predictions."""
        claim = "We forecast a 50% revenue increase next quarter"
        context = {"prediction": True}

        result = self.validator._validate_critical(claim, context)

        self.assertEqual(result.validation_type, ValidationType.CRITICAL)
        self.assertIn('risk_level', result.details)
        self.assertIn(result.details['risk_level'], ['high', 'medium'])

    def test_critical_validation_compliance(self):
        """Test regulatory compliance checking."""
        claim = "Compliance with SEC regulations"
        context = {"regulatory": True}

        result = self.validator._validate_critical(claim, context)

        self.assertIn('compliance_passed', result.details)
        self.assertIsInstance(result.details['compliance_passed'], bool)

    def test_full_validation_all_types(self):
        """Test complete validation with all check types."""
        claim = "Revenue increased by 20% therefore profit margin improved"
        context = {"year": 2024}

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)
        self.assertEqual(len(report.results), 3)  # All three validation types
        self.assertIn('confidence_score', report.__dict__)
        self.assertIn('risk_level', report.__dict__)

    def test_validation_selective_types(self):
        """Test validation with selective check types."""
        claim = "The calculation shows 100 + 50 = 150"
        context = {}

        report = self.validator.validate(
            claim,
            context,
            validation_types=[ValidationType.MATHEMATICAL]
        )

        self.assertEqual(len(report.results), 1)
        self.assertEqual(report.results[0].validation_type, ValidationType.MATHEMATICAL)

    def test_severity_determination_critical(self):
        """Test severity determination for critical validation."""
        severity = self.validator._determine_severity(0.65, ValidationType.CRITICAL)
        self.assertEqual(severity, ValidationSeverity.CRITICAL)

    def test_severity_determination_high(self):
        """Test severity determination for high severity."""
        severity = self.validator._determine_severity(0.55, ValidationType.MATHEMATICAL)
        self.assertEqual(severity, ValidationSeverity.HIGH)

    def test_severity_determination_low(self):
        """Test severity determination for low severity."""
        severity = self.validator._determine_severity(0.90, ValidationType.MATHEMATICAL)
        self.assertEqual(severity, ValidationSeverity.LOW)

    def test_extract_numbers(self):
        """Test number extraction from text."""
        text = "Revenue: $123.45M, Profit: 67.8%, Growth: -5.2%"
        numbers = self.validator._extract_numbers(text)

        self.assertGreater(len(numbers), 0)
        self.assertIn(123.45, numbers)
        self.assertIn(67.8, numbers)
        self.assertIn(-5.2, numbers)

    def test_extract_numbers_scientific(self):
        """Test extraction of scientific notation."""
        text = "Value is 1.23e6 or 4.5E-3"
        numbers = self.validator._extract_numbers(text)

        self.assertIn(1.23e6, numbers)
        self.assertIn(4.5e-3, numbers)

    def test_risk_assessment_forecast(self):
        """Test risk assessment for forecasts."""
        claim = "We forecast revenue growth of 30%"
        context = {}

        risk_level = self.validator._assess_risk_level(claim, context)
        self.assertEqual(risk_level, "high")

    def test_risk_assessment_general(self):
        """Test risk assessment for general statements."""
        claim = "The company has a strong balance sheet"
        context = {}

        risk_level = self.validator._assess_risk_level(claim, context)
        self.assertEqual(risk_level, "medium")

    def test_report_generation_all_pass(self):
        """Test report generation when all validations pass."""
        results = [
            ValidationResult(
                validation_type=ValidationType.MATHEMATICAL,
                passed=True,
                confidence=0.95,
                severity=ValidationSeverity.LOW,
                message="Math check passed"
            ),
            ValidationResult(
                validation_type=ValidationType.LOGICAL,
                passed=True,
                confidence=0.90,
                severity=ValidationSeverity.LOW,
                message="Logic check passed"
            )
        ]

        report = self.validator._generate_report(results)

        self.assertTrue(report.overall_passed)
        self.assertGreater(report.confidence_score, 0.85)
        self.assertIn("All validations passed", report.recommendations[0])

    def test_report_generation_with_failures(self):
        """Test report generation with validation failures."""
        results = [
            ValidationResult(
                validation_type=ValidationType.MATHEMATICAL,
                passed=False,
                confidence=0.60,
                severity=ValidationSeverity.HIGH,
                message="Math check failed"
            )
        ]

        report = self.validator._generate_report(results)

        self.assertFalse(report.overall_passed)
        self.assertLess(report.confidence_score, 0.85)
        self.assertGreater(len(report.recommendations), 0)
        self.assertIn("Review numerical", report.recommendations[0])

    def test_calculate_risk_level(self):
        """Test overall risk level calculation."""
        results = [
            ValidationResult(
                validation_type=ValidationType.MATHEMATICAL,
                passed=True,
                confidence=0.95,
                severity=ValidationSeverity.LOW,
                message="Test"
            ),
            ValidationResult(
                validation_type=ValidationType.CRITICAL,
                passed=False,
                confidence=0.50,
                severity=ValidationSeverity.CRITICAL,
                message="Test"
            )
        ]

        risk_level = self.validator._calculate_risk_level(results)
        self.assertEqual(risk_level, "critical")


class TestValidationEdgeCases(unittest.TestCase):
    """Test edge cases and failure modes."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FACTValidator(enable_logging=False)

    def test_empty_claim(self):
        """Test validation with empty claim."""
        report = self.validator.validate("", {})

        self.assertIsInstance(report, ValidationReport)
        self.assertGreater(len(report.results), 0)

    def test_very_long_claim(self):
        """Test validation with very long claim."""
        claim = "Revenue " * 1000 + "increased significantly"
        context = {}

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)

    def test_special_characters(self):
        """Test validation with special characters."""
        claim = "Revenue: $100M (Q1) → $125M (Q2) ≈ 25% ↑"
        context = {}

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)

    def test_missing_context(self):
        """Test validation with minimal context."""
        claim = "Revenue increased"
        context = {}

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)
        self.assertIsNotNone(report.confidence_score)

    def test_contradictory_claims(self):
        """Test validation of contradictory statements."""
        claim = "Revenue increased but revenue decreased"
        context = {}

        result = self.validator._validate_logical(claim, context)

        # Should detect contradiction
        self.assertIn('contradictions', result.details)

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        claim = "Revenue: ¥100万, Profit: €50千, Growth: ₹25千"
        context = {}

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)

    def test_multiple_validations_same_claim(self):
        """Test running validation multiple times on same claim."""
        claim = "Revenue increased by 20%"
        context = {}

        report1 = self.validator.validate(claim, context)
        report2 = self.validator.validate(claim, context)

        # Should produce consistent results
        self.assertEqual(
            len(report1.results),
            len(report2.results)
        )


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for complete validation workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FACTValidator(enable_logging=False)

    def test_financial_forecast_validation(self):
        """Test validation of financial forecast."""
        claim = """
        Based on Q1-Q3 performance showing 15% YoY growth,
        we forecast Q4 revenue of $150M, representing 12% growth.
        This assumes market conditions remain stable.
        """
        context = {
            "historical_data": [100, 110, 125],
            "forecast_period": "Q4",
            "year": 2024
        }

        report = self.validator.validate(claim, context)

        self.assertIsInstance(report, ValidationReport)
        self.assertEqual(len(report.results), 3)
        self.assertIsNotNone(report.risk_level)
        self.assertGreater(len(report.recommendations), 0)

    def test_market_prediction_validation(self):
        """Test validation of market prediction."""
        claim = """
        The stock price is likely to increase by 20-30% over the next
        quarter due to strong fundamentals and positive market sentiment.
        """
        context = {
            "prediction_type": "market",
            "time_horizon": 90
        }

        report = self.validator.validate(claim, context)

        self.assertIn(report.risk_level, ["high", "critical"])
        self.assertTrue(any("disclaimer" in r.lower() for r in report.recommendations))

    def test_complex_calculation_validation(self):
        """Test validation of complex calculations."""
        claim = """
        EBITDA margin improved from 15.2% to 18.7%, calculated as
        (EBITDA / Revenue). With revenue of $500M and EBITDA of $93.5M,
        this represents a 23% increase in operational efficiency.
        """
        context = {
            "verification_required": True
        }

        report = self.validator.validate(
            claim,
            context,
            validation_types=[ValidationType.MATHEMATICAL]
        )

        math_result = report.results[0]
        self.assertEqual(math_result.validation_type, ValidationType.MATHEMATICAL)
        self.assertIn('calculations_checked', math_result.details)


if __name__ == '__main__':
    unittest.main()

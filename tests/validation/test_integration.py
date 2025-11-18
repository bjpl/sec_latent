"""
Integration tests for FACT and GOALIE working together.

Tests the complete validation pipeline with both frameworks.
"""

import unittest
from src.validation.fact import FACTValidator, ValidationType
from src.validation.goalie import GOALIEProtection
from src.validation.metrics import MetricsCalculator, ThresholdConfig


class TestFACTGOALIEIntegration(unittest.TestCase):
    """Integration tests for FACT + GOALIE pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.fact = FACTValidator(enable_logging=False)
        self.goalie = GOALIEProtection(enable_logging=False)
        self.metrics = MetricsCalculator()

    def test_complete_validation_pipeline(self):
        """Test complete validation pipeline from claim to adjusted output."""
        # Original claim
        claim = "We forecast Q4 revenue of $150M, representing 25% growth"
        context = {
            "historical_revenue": [100, 110, 120],
            "time_horizon": 90,
            "uncertainty_high": True
        }

        # Step 1: FACT validation
        fact_report = self.fact.validate(claim, context)

        self.assertIsNotNone(fact_report)
        self.assertEqual(len(fact_report.results), 3)

        # Step 2: Convert FACT results to model outputs for GOALIE
        model_outputs = {
            "fact_validator": {
                "confidence": fact_report.confidence_score
            }
        }

        # Step 3: GOALIE protection
        prediction = {"revenue": 150.0, "growth": 0.25}
        goalie_result = self.goalie.protect(prediction, context, model_outputs)

        self.assertIsNotNone(goalie_result)
        self.assertLess(goalie_result.adjustment_factor, 1.0)  # Should be adjusted

        # Step 4: Verify adjustments are applied
        self.assertIn('_goalie_disclaimer', goalie_result.adjusted_prediction)

    def test_high_confidence_low_risk_flow(self):
        """Test pipeline with high confidence, low risk scenario."""
        claim = "Historical average revenue growth was 15% over past 5 years"
        context = {
            "historical_data": True,
            "time_horizon": 0  # Historical, not forecast
        }

        # FACT validation
        fact_report = self.fact.validate(claim, context)

        # Should have high confidence
        self.assertGreater(fact_report.confidence_score, 0.8)

        # GOALIE protection
        model_outputs = {
            "fact": {"confidence": fact_report.confidence_score},
            "model2": {"confidence": 0.92}
        }

        prediction = {"average_growth": 0.15}
        goalie_result = self.goalie.protect(prediction, context, model_outputs)

        # Should have minimal adjustment
        self.assertGreater(goalie_result.adjustment_factor, 0.85)
        self.assertTrue(goalie_result.should_display)

    def test_low_confidence_high_risk_flow(self):
        """Test pipeline with low confidence, high risk scenario."""
        claim = "Stock price predicted to triple within 6 months"
        context = {
            "prediction": True,
            "time_horizon": 180,
            "uncertainty_high": True,
            "historical_volatility": 0.9
        }

        # FACT validation
        fact_report = self.fact.validate(claim, context)

        # GOALIE protection with low confidence
        model_outputs = {
            "fact": {"confidence": 0.5},
            "model2": {"confidence": 0.45}
        }

        prediction = {"price_multiplier": 3.0}
        goalie_result = self.goalie.protect(prediction, context, model_outputs)

        # Should have significant adjustment
        self.assertLess(goalie_result.adjustment_factor, 0.7)
        # May not display due to high risk + low confidence
        # (depends on exact scores)

    def test_mathematical_validation_with_goalie_adjustment(self):
        """Test mathematical validation followed by GOALIE adjustment."""
        claim = "Profit margin improved from 10% to 15%, a 50% increase"
        context = {"verification_required": True}

        # FACT mathematical validation
        fact_report = self.fact.validate(
            claim,
            context,
            validation_types=[ValidationType.MATHEMATICAL]
        )

        # Extract mathematical confidence
        math_result = fact_report.results[0]

        # GOALIE adjustment
        model_outputs = {"fact_math": {"confidence": math_result.confidence}}
        prediction = {"margin_increase_pct": 50.0}
        goalie_result = self.goalie.protect(prediction, context, model_outputs)

        # Verify both systems worked
        self.assertIsNotNone(math_result.details)
        self.assertIsNotNone(goalie_result.adjusted_prediction)

    def test_multi_model_consensus_with_fact(self):
        """Test multiple models with FACT providing one vote."""
        claim = "Revenue growth expected to reach 20%"
        context = {"forecast": True}

        # FACT validation
        fact_report = self.fact.validate(claim, context)

        # Multiple model outputs including FACT
        model_outputs = {
            "fact_validator": {"confidence": fact_report.confidence_score},
            "financial_model": {"confidence": 0.82},
            "ml_model": {"confidence": 0.78},
            "expert_model": {"confidence": 0.85}
        }

        prediction = {"growth": 0.20}
        goalie_result = self.goalie.protect(prediction, context, model_outputs)

        # Should have good agreement with 4 models
        self.assertGreater(goalie_result.confidence_score.agreement_level, 0.7)

    def test_validation_metrics_tracking(self):
        """Test tracking metrics across multiple validations."""
        test_cases = [
            ("Revenue increased 10%", {"year": 2024}, True),
            ("Profit will triple", {"forecast": True}, False),
            ("Historical growth: 15%", {"historical": True}, True),
            ("Market will crash", {"prediction": True}, False)
        ]

        predictions = []
        actuals = []
        confidences = []

        for claim, context, expected_reliable in test_cases:
            # FACT + GOALIE pipeline
            fact_report = self.fact.validate(claim, context)
            model_outputs = {"fact": {"confidence": fact_report.confidence_score}}
            goalie_result = self.goalie.protect(claim, context, model_outputs)

            predictions.append(goalie_result.should_display)
            actuals.append(expected_reliable)
            confidences.append(goalie_result.confidence_score.overall_confidence)

        # Calculate metrics
        metrics = self.metrics.calculate_metrics(predictions, actuals, confidences)

        # Verify metrics are calculated
        self.assertIsNotNone(metrics.accuracy)
        self.assertIsNotNone(metrics.precision)
        self.assertIsNotNone(metrics.recall)


class TestFailureModes(unittest.TestCase):
    """Test failure modes and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.fact = FACTValidator(enable_logging=False)
        self.goalie = GOALIEProtection(enable_logging=False)

    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        # FACT with empty claim
        fact_report = self.fact.validate("", {})
        self.assertIsNotNone(fact_report)

        # GOALIE with empty prediction
        goalie_result = self.goalie.protect("", {})
        self.assertIsNotNone(goalie_result)

    def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        # Malformed context
        claim = "Test claim"
        context = {"invalid": None, "broken": {}}

        fact_report = self.fact.validate(claim, context)
        self.assertIsNotNone(fact_report)

        goalie_result = self.goalie.protect(claim, context)
        self.assertIsNotNone(goalie_result)

    def test_extreme_values_handling(self):
        """Test handling of extreme values."""
        claim = "Revenue: $999999999999999"
        context = {"extreme_value": True}

        fact_report = self.fact.validate(claim, context)
        self.assertIsNotNone(fact_report)

        prediction = 999999999999999
        goalie_result = self.goalie.protect(prediction, context)
        self.assertIsNotNone(goalie_result)

    def test_cascading_failures(self):
        """Test behavior when multiple validation stages fail."""
        claim = "Invalid illogical forecast with wrong math"
        context = {
            "uncertainty_high": True,
            "data_quality": 0.2,
            "sample_size": 5
        }

        # All FACT validations should flag issues
        fact_report = self.fact.validate(claim, context)

        # GOALIE should apply maximum protection
        model_outputs = {
            "fact": {"confidence": fact_report.confidence_score}
        }
        goalie_result = self.goalie.protect(claim, context, model_outputs)

        # Should have low confidence and high adjustment
        self.assertLess(goalie_result.confidence_score.overall_confidence, 0.7)
        self.assertLess(goalie_result.adjustment_factor, 0.7)


class TestPerformance(unittest.TestCase):
    """Performance and scalability tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.fact = FACTValidator(enable_logging=False)
        self.goalie = GOALIEProtection(enable_logging=False)

    def test_batch_validation_performance(self):
        """Test performance with batch validations."""
        claims = [
            f"Revenue forecast {i}: ${100 + i}M"
            for i in range(50)
        ]
        context = {"batch": True}

        # Time multiple validations
        import time
        start = time.time()

        for claim in claims:
            fact_report = self.fact.validate(claim, context)
            self.assertIsNotNone(fact_report)

        duration = time.time() - start

        # Should complete in reasonable time
        # (exact threshold depends on system)
        self.assertLess(duration, 30.0)  # 30 seconds for 50 validations

    def test_large_context_handling(self):
        """Test handling of large context data."""
        claim = "Revenue analysis"
        context = {
            "historical_data": list(range(1000)),
            "metadata": {f"key_{i}": f"value_{i}" for i in range(100)},
            "large_text": "x" * 10000
        }

        # Should handle large context
        fact_report = self.fact.validate(claim, context)
        self.assertIsNotNone(fact_report)

        goalie_result = self.goalie.protect(claim, context)
        self.assertIsNotNone(goalie_result)


if __name__ == '__main__':
    unittest.main()

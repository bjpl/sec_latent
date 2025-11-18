"""
Comprehensive tests for GOALIE protection system.

Tests cover:
- Risk assessment filters
- Confidence scoring
- Prediction adjustment
- Edge cases and failure modes
"""

import unittest
from unittest.mock import Mock, patch
from src.validation.goalie import (
    GOALIEProtection,
    RiskCategory,
    RiskLevel,
    RiskAssessment,
    ConfidenceScore,
    AdjustedPrediction
)


class TestGOALIEProtection(unittest.TestCase):
    """Test suite for GOALIE protection system."""

    def setUp(self):
        """Set up test fixtures."""
        self.goalie = GOALIEProtection(
            risk_threshold=0.7,
            confidence_threshold=0.8,
            min_model_agreement=0.75,
            enable_logging=False
        )

    def test_initialization(self):
        """Test GOALIE initialization."""
        self.assertEqual(self.goalie.risk_threshold, 0.7)
        self.assertEqual(self.goalie.confidence_threshold, 0.8)
        self.assertEqual(self.goalie.min_model_agreement, 0.75)

    def test_risk_categorization_financial_forecast(self):
        """Test categorization of financial forecasts."""
        prediction = "We forecast revenue of $100M next quarter"
        context = {}

        category = self.goalie._categorize_risk(prediction, context)
        self.assertEqual(category, RiskCategory.FINANCIAL_FORECAST)

    def test_risk_categorization_market_prediction(self):
        """Test categorization of market predictions."""
        prediction = "Stock price will increase by 20%"
        context = {}

        category = self.goalie._categorize_risk(prediction, context)
        self.assertEqual(category, RiskCategory.MARKET_PREDICTION)

    def test_risk_categorization_valuation(self):
        """Test categorization of valuations."""
        prediction = "Company valuation estimated at $500M"
        context = {}

        category = self.goalie._categorize_risk(prediction, context)
        self.assertEqual(category, RiskCategory.COMPANY_VALUATION)

    def test_risk_categorization_regulatory(self):
        """Test categorization of regulatory statements."""
        prediction = "Compliance requirements met for all regulations"
        context = {}

        category = self.goalie._categorize_risk(prediction, context)
        self.assertEqual(category, RiskCategory.REGULATORY_COMPLIANCE)

    def test_risk_score_calculation_high(self):
        """Test risk score calculation for high-risk categories."""
        prediction = "Stock price forecast"
        context = {}
        category = RiskCategory.MARKET_PREDICTION

        risk_score = self.goalie._calculate_risk_score(prediction, context, category)

        self.assertGreater(risk_score, 0.7)
        self.assertLessEqual(risk_score, 1.0)

    def test_risk_score_calculation_low(self):
        """Test risk score calculation for low-risk categories."""
        prediction = "General market analysis"
        context = {}
        category = RiskCategory.GENERAL_ANALYSIS

        risk_score = self.goalie._calculate_risk_score(prediction, context, category)

        self.assertLess(risk_score, 0.6)

    def test_risk_score_adjustment_uncertainty(self):
        """Test risk score adjustment for high uncertainty."""
        prediction = "Forecast"
        context = {"uncertainty_high": True, "historical_volatility": 0.8}
        category = RiskCategory.FINANCIAL_FORECAST

        risk_score = self.goalie._calculate_risk_score(prediction, context, category)

        # Should be higher due to uncertainty flags
        self.assertGreater(risk_score, 0.8)

    def test_risk_level_determination(self):
        """Test risk level determination from scores."""
        self.assertEqual(
            self.goalie._determine_risk_level(0.90),
            RiskLevel.CRITICAL
        )
        self.assertEqual(
            self.goalie._determine_risk_level(0.75),
            RiskLevel.HIGH
        )
        self.assertEqual(
            self.goalie._determine_risk_level(0.55),
            RiskLevel.MODERATE
        )
        self.assertEqual(
            self.goalie._determine_risk_level(0.35),
            RiskLevel.LOW
        )
        self.assertEqual(
            self.goalie._determine_risk_level(0.20),
            RiskLevel.MINIMAL
        )

    def test_risk_assessment_complete(self):
        """Test complete risk assessment."""
        prediction = "Revenue forecast of $150M represents 25% growth"
        context = {"time_horizon": 90}

        assessment = self.goalie.assess_risk(prediction, context)

        self.assertIsInstance(assessment, RiskAssessment)
        self.assertIsInstance(assessment.risk_level, RiskLevel)
        self.assertIsInstance(assessment.risk_category, RiskCategory)
        self.assertGreater(len(assessment.factors), 0)
        self.assertGreater(len(assessment.mitigation_strategies), 0)

    def test_confidence_scoring_high_agreement(self):
        """Test confidence scoring with high model agreement."""
        prediction = "Test prediction"
        model_outputs = {
            "model1": {"confidence": 0.9},
            "model2": {"confidence": 0.88},
            "model3": {"confidence": 0.92}
        }

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertIsInstance(confidence, ConfidenceScore)
        self.assertGreater(confidence.overall_confidence, 0.85)
        self.assertGreater(confidence.agreement_level, 0.9)
        self.assertTrue(confidence.reliable)

    def test_confidence_scoring_low_agreement(self):
        """Test confidence scoring with low model agreement."""
        prediction = "Test prediction"
        model_outputs = {
            "model1": {"confidence": 0.9},
            "model2": {"confidence": 0.5},
            "model3": {"confidence": 0.6}
        }

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertLess(confidence.agreement_level, 0.8)
        self.assertGreater(confidence.variance, 0.02)

    def test_confidence_scoring_single_model(self):
        """Test confidence scoring with single model."""
        prediction = "Test prediction"
        model_outputs = {"model1": {"confidence": 0.85}}

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertIsInstance(confidence, ConfidenceScore)
        self.assertEqual(confidence.agreement_level, 1.0)  # Single model = perfect agreement

    def test_confidence_scoring_no_models(self):
        """Test confidence scoring with no models."""
        prediction = "Test prediction"
        model_outputs = {}

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertEqual(confidence.overall_confidence, 0.5)  # Default

    def test_adjustment_factor_high_risk_low_confidence(self):
        """Test adjustment factor for high risk and low confidence."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            risk_category=RiskCategory.MARKET_PREDICTION,
            risk_score=0.85,
            factors=["High uncertainty"],
            mitigation_strategies=[]
        )

        confidence_score = ConfidenceScore(
            overall_confidence=0.6,
            model_scores={"model1": 0.6},
            agreement_level=0.6,
            variance=0.1,
            reliable=False
        )

        adjustment = self.goalie._calculate_adjustment_factor(
            risk_assessment,
            confidence_score
        )

        # Should be significantly reduced
        self.assertLess(adjustment, 0.6)

    def test_adjustment_factor_low_risk_high_confidence(self):
        """Test adjustment factor for low risk and high confidence."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_category=RiskCategory.GENERAL_ANALYSIS,
            risk_score=0.3,
            factors=[],
            mitigation_strategies=[]
        )

        confidence_score = ConfidenceScore(
            overall_confidence=0.95,
            model_scores={"model1": 0.95},
            agreement_level=0.98,
            variance=0.01,
            reliable=True
        )

        adjustment = self.goalie._calculate_adjustment_factor(
            risk_assessment,
            confidence_score
        )

        # Should be close to 1.0
        self.assertGreater(adjustment, 0.85)

    def test_prediction_adjustment_numerical(self):
        """Test adjustment of numerical predictions."""
        prediction = 100.0
        adjustment_factor = 0.8

        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.MODERATE,
            risk_category=RiskCategory.FINANCIAL_FORECAST,
            risk_score=0.6,
            factors=[],
            mitigation_strategies=[]
        )

        adjusted = self.goalie._apply_adjustment(
            prediction,
            adjustment_factor,
            risk_assessment
        )

        self.assertEqual(adjusted, 80.0)

    def test_prediction_adjustment_dict(self):
        """Test adjustment of dictionary predictions."""
        prediction = {
            "revenue": 100.0,
            "profit": 25.0,
            "description": "Forecast"
        }
        adjustment_factor = 0.9

        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_category=RiskCategory.FINANCIAL_FORECAST,
            risk_score=0.4,
            factors=[],
            mitigation_strategies=[]
        )

        adjusted = self.goalie._apply_adjustment(
            prediction,
            adjustment_factor,
            risk_assessment
        )

        self.assertEqual(adjusted["revenue"], 90.0)
        self.assertEqual(adjusted["profit"], 22.5)
        self.assertEqual(adjusted["description"], "Forecast")
        self.assertIn("_goalie_disclaimer", adjusted)

    def test_disclaimer_generation_critical(self):
        """Test disclaimer generation for critical risk."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            risk_category=RiskCategory.MARKET_PREDICTION,
            risk_score=0.95,
            factors=[],
            mitigation_strategies=[]
        )

        disclaimer = self.goalie._generate_disclaimer(risk_assessment)

        self.assertIn("CRITICAL", disclaimer)
        self.assertIn("⚠️", disclaimer)

    def test_disclaimer_generation_moderate(self):
        """Test disclaimer generation for moderate risk."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.MODERATE,
            risk_category=RiskCategory.GENERAL_ANALYSIS,
            risk_score=0.5,
            factors=[],
            mitigation_strategies=[]
        )

        disclaimer = self.goalie._generate_disclaimer(risk_assessment)

        self.assertIn("forward-looking", disclaimer)

    def test_should_display_reliable(self):
        """Test display decision for reliable predictions."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_category=RiskCategory.GENERAL_ANALYSIS,
            risk_score=0.3,
            factors=[],
            mitigation_strategies=[]
        )

        confidence_score = ConfidenceScore(
            overall_confidence=0.9,
            model_scores={},
            agreement_level=0.9,
            variance=0.05,
            reliable=True
        )

        should_display = self.goalie._should_display(
            risk_assessment,
            confidence_score
        )

        self.assertTrue(should_display)

    def test_should_display_critical_low_confidence(self):
        """Test display decision for critical risk with low confidence."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            risk_category=RiskCategory.MARKET_PREDICTION,
            risk_score=0.95,
            factors=[],
            mitigation_strategies=[]
        )

        confidence_score = ConfidenceScore(
            overall_confidence=0.5,
            model_scores={},
            agreement_level=0.5,
            variance=0.1,
            reliable=False
        )

        should_display = self.goalie._should_display(
            risk_assessment,
            confidence_score
        )

        self.assertFalse(should_display)

    def test_should_display_high_variance(self):
        """Test display decision for high variance."""
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.MODERATE,
            risk_category=RiskCategory.FINANCIAL_FORECAST,
            risk_score=0.6,
            factors=[],
            mitigation_strategies=[]
        )

        confidence_score = ConfidenceScore(
            overall_confidence=0.8,
            model_scores={},
            agreement_level=0.8,
            variance=0.35,  # High variance
            reliable=True
        )

        should_display = self.goalie._should_display(
            risk_assessment,
            confidence_score
        )

        self.assertFalse(should_display)

    def test_full_protection_workflow(self):
        """Test complete protection workflow."""
        prediction = {"revenue_forecast": 150.0, "confidence": "high"}
        context = {"time_horizon": 90, "uncertainty_high": True}
        model_outputs = {
            "model1": {"confidence": 0.85},
            "model2": {"confidence": 0.82}
        }

        result = self.goalie.protect(prediction, context, model_outputs)

        self.assertIsInstance(result, AdjustedPrediction)
        self.assertIsNotNone(result.original_prediction)
        self.assertIsNotNone(result.adjusted_prediction)
        self.assertIsInstance(result.confidence_score, ConfidenceScore)
        self.assertIsInstance(result.risk_assessment, RiskAssessment)
        self.assertGreater(len(result.explanation), 0)
        self.assertIsInstance(result.should_display, bool)


class TestGOALIEEdgeCases(unittest.TestCase):
    """Test edge cases and failure modes for GOALIE."""

    def setUp(self):
        """Set up test fixtures."""
        self.goalie = GOALIEProtection(enable_logging=False)

    def test_empty_prediction(self):
        """Test protection with empty prediction."""
        result = self.goalie.protect("", {})

        self.assertIsInstance(result, AdjustedPrediction)

    def test_none_prediction(self):
        """Test protection with None prediction."""
        result = self.goalie.protect(None, {})

        self.assertIsInstance(result, AdjustedPrediction)

    def test_complex_nested_prediction(self):
        """Test protection with complex nested structure."""
        prediction = {
            "forecast": {
                "revenue": {"q1": 100, "q2": 110},
                "expenses": {"q1": 80, "q2": 85}
            },
            "metadata": {"source": "model_v2"}
        }
        context = {}

        result = self.goalie.protect(prediction, context)

        self.assertIsInstance(result, AdjustedPrediction)

    def test_extreme_risk_score(self):
        """Test handling of extreme risk scores."""
        prediction = "Critical market prediction"
        context = {
            "uncertainty_high": True,
            "historical_volatility": 1.0
        }

        assessment = self.goalie.assess_risk(prediction, context)

        self.assertLessEqual(assessment.risk_score, 1.0)
        self.assertEqual(assessment.risk_level, RiskLevel.CRITICAL)

    def test_zero_confidence(self):
        """Test handling of zero confidence scores."""
        prediction = "Test"
        model_outputs = {
            "model1": {"confidence": 0.0}
        }

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertEqual(confidence.overall_confidence, 0.0)
        self.assertFalse(confidence.reliable)

    def test_conflicting_model_outputs(self):
        """Test handling of conflicting model outputs."""
        prediction = "Test"
        model_outputs = {
            "model1": {"confidence": 0.95},
            "model2": {"confidence": 0.05}
        }

        confidence = self.goalie.calculate_confidence(prediction, model_outputs)

        self.assertGreater(confidence.variance, 0.2)
        self.assertLess(confidence.agreement_level, 0.7)


class TestGOALIEIntegration(unittest.TestCase):
    """Integration tests for GOALIE protection system."""

    def setUp(self):
        """Set up test fixtures."""
        self.goalie = GOALIEProtection(enable_logging=False)

    def test_financial_forecast_protection(self):
        """Test protection of financial forecasts."""
        prediction = {
            "revenue": 150.0,
            "growth_rate": 0.25,
            "period": "Q4 2024"
        }
        context = {
            "prediction_type": "financial_forecast",
            "time_horizon": 90,
            "uncertainty_high": True
        }
        model_outputs = {
            "financial_model": {"confidence": 0.82},
            "ml_model": {"confidence": 0.78}
        }

        result = self.goalie.protect(prediction, context, model_outputs)

        # Should have conservative adjustment
        self.assertLess(result.adjustment_factor, 1.0)
        self.assertEqual(
            result.risk_assessment.risk_category,
            RiskCategory.FINANCIAL_FORECAST
        )
        self.assertIn("_goalie_disclaimer", result.adjusted_prediction)

    def test_market_prediction_protection(self):
        """Test protection of market predictions."""
        prediction = "Stock price expected to increase 30-40%"
        context = {"market_volatility": "high"}
        model_outputs = {
            "market_model": {"confidence": 0.65}
        }

        result = self.goalie.protect(prediction, context, model_outputs)

        # High risk category
        self.assertIn(
            result.risk_assessment.risk_level,
            [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        # Low confidence should reduce display likelihood
        self.assertLessEqual(result.confidence_score.overall_confidence, 0.7)

    def test_low_risk_high_confidence_protection(self):
        """Test protection of low-risk, high-confidence analysis."""
        prediction = {
            "analysis": "Historical revenue growth averaged 15% annually",
            "confidence": 0.95
        }
        context = {"historical_data": True}
        model_outputs = {
            "model1": {"confidence": 0.95},
            "model2": {"confidence": 0.93},
            "model3": {"confidence": 0.94}
        }

        result = self.goalie.protect(prediction, context, model_outputs)

        # Should have minimal adjustment
        self.assertGreater(result.adjustment_factor, 0.85)
        self.assertTrue(result.should_display)
        self.assertTrue(result.confidence_score.reliable)


if __name__ == '__main__':
    unittest.main()

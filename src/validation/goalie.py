"""
GOALIE Protection System

GOALIE = Guarded Output Assessment and Liability-minimizing Intelligence Engine
This module provides risk assessment, confidence scoring, and prediction adjustment
to minimize false positives and protect against high-risk outputs.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class RiskCategory(Enum):
    """Risk categories for predictions."""
    FINANCIAL_FORECAST = "financial_forecast"
    MARKET_PREDICTION = "market_prediction"
    COMPANY_VALUATION = "company_valuation"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    GENERAL_ANALYSIS = "general_analysis"


class RiskLevel(Enum):
    """Risk levels for outputs."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_level: RiskLevel
    risk_category: RiskCategory
    risk_score: float
    factors: List[str]
    mitigation_strategies: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConfidenceScore:
    """Multi-model confidence score."""
    overall_confidence: float
    model_scores: Dict[str, float]
    agreement_level: float
    variance: float
    reliable: bool


@dataclass
class AdjustedPrediction:
    """Prediction adjusted for risk and confidence."""
    original_prediction: Any
    adjusted_prediction: Any
    adjustment_factor: float
    confidence_score: ConfidenceScore
    risk_assessment: RiskAssessment
    explanation: str
    should_display: bool


class GOALIEProtection:
    """
    GOALIE Protection System for risk mitigation and output calibration.

    This system provides three layers of protection:
    1. Risk Assessment Filters - Identify high-risk predictions
    2. Confidence Scoring - Multi-model agreement metrics
    3. Prediction Adjustment - Calibrate outputs to minimize false positives
    """

    def __init__(
        self,
        risk_threshold: float = 0.7,
        confidence_threshold: float = 0.8,
        min_model_agreement: float = 0.75,
        enable_logging: bool = True
    ):
        """
        Initialize GOALIE protection system.

        Args:
            risk_threshold: Maximum acceptable risk score
            confidence_threshold: Minimum required confidence
            min_model_agreement: Minimum model agreement for reliability
            enable_logging: Enable detailed logging
        """
        self.risk_threshold = risk_threshold
        self.confidence_threshold = confidence_threshold
        self.min_model_agreement = min_model_agreement
        self.logger = logging.getLogger(__name__)
        if enable_logging:
            self.logger.setLevel(logging.INFO)

    def protect(
        self,
        prediction: Any,
        context: Dict[str, Any],
        model_outputs: Optional[Dict[str, Any]] = None
    ) -> AdjustedPrediction:
        """
        Apply GOALIE protection to a prediction.

        Args:
            prediction: The prediction to protect
            context: Context information
            model_outputs: Outputs from multiple models (for confidence scoring)

        Returns:
            AdjustedPrediction with risk assessment and confidence scoring
        """
        # Step 1: Risk Assessment
        risk_assessment = self.assess_risk(prediction, context)

        # Step 2: Confidence Scoring
        confidence_score = self.calculate_confidence(prediction, model_outputs or {})

        # Step 3: Prediction Adjustment
        adjusted_prediction = self.adjust_prediction(
            prediction,
            risk_assessment,
            confidence_score,
            context
        )

        return adjusted_prediction

    def assess_risk(
        self,
        prediction: Any,
        context: Dict[str, Any]
    ) -> RiskAssessment:
        """
        Assess risk level of a prediction.

        This evaluates:
        - Type of prediction (financial, market, etc.)
        - Confidence intervals
        - Historical accuracy
        - Potential impact
        - Regulatory implications
        """
        self.logger.info("Assessing prediction risk")

        # Determine risk category
        risk_category = self._categorize_risk(prediction, context)

        # Calculate risk score
        risk_score = self._calculate_risk_score(prediction, context, risk_category)

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Identify risk factors
        factors = self._identify_risk_factors(prediction, context, risk_category)

        # Generate mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(
            risk_level,
            risk_category,
            factors
        )

        return RiskAssessment(
            risk_level=risk_level,
            risk_category=risk_category,
            risk_score=risk_score,
            factors=factors,
            mitigation_strategies=mitigation_strategies
        )

    def calculate_confidence(
        self,
        prediction: Any,
        model_outputs: Dict[str, Any]
    ) -> ConfidenceScore:
        """
        Calculate multi-model confidence score.

        This considers:
        - Individual model confidence scores
        - Agreement between models
        - Variance in predictions
        - Historical model performance
        """
        self.logger.info("Calculating confidence score")

        # Extract individual model scores
        model_scores = self._extract_model_scores(model_outputs)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(model_scores)

        # Calculate agreement level
        agreement_level = self._calculate_agreement_level(model_outputs)

        # Calculate variance
        variance = self._calculate_variance(model_outputs)

        # Determine reliability
        reliable = (
            overall_confidence >= self.confidence_threshold and
            agreement_level >= self.min_model_agreement and
            variance < 0.2
        )

        return ConfidenceScore(
            overall_confidence=overall_confidence,
            model_scores=model_scores,
            agreement_level=agreement_level,
            variance=variance,
            reliable=reliable
        )

    def adjust_prediction(
        self,
        prediction: Any,
        risk_assessment: RiskAssessment,
        confidence_score: ConfidenceScore,
        context: Dict[str, Any]
    ) -> AdjustedPrediction:
        """
        Adjust prediction based on risk and confidence.

        This applies:
        - Conservative adjustments for high-risk predictions
        - Confidence-based scaling
        - Disclaimer additions
        - Display filtering
        """
        self.logger.info("Adjusting prediction for risk and confidence")

        # Determine adjustment factor
        adjustment_factor = self._calculate_adjustment_factor(
            risk_assessment,
            confidence_score
        )

        # Apply adjustment
        adjusted_pred = self._apply_adjustment(
            prediction,
            adjustment_factor,
            risk_assessment
        )

        # Generate explanation
        explanation = self._generate_explanation(
            risk_assessment,
            confidence_score,
            adjustment_factor
        )

        # Determine if should display
        should_display = self._should_display(
            risk_assessment,
            confidence_score
        )

        return AdjustedPrediction(
            original_prediction=prediction,
            adjusted_prediction=adjusted_pred,
            adjustment_factor=adjustment_factor,
            confidence_score=confidence_score,
            risk_assessment=risk_assessment,
            explanation=explanation,
            should_display=should_display
        )

    # Risk Assessment Methods

    def _categorize_risk(
        self,
        prediction: Any,
        context: Dict[str, Any]
    ) -> RiskCategory:
        """Categorize the type of risk."""
        prediction_str = str(prediction).lower()

        # Check for financial forecasts
        if any(kw in prediction_str for kw in ['forecast', 'project', 'estimate', 'expect']):
            if any(kw in prediction_str for kw in ['revenue', 'earnings', 'profit', 'loss']):
                return RiskCategory.FINANCIAL_FORECAST

        # Check for market predictions
        if any(kw in prediction_str for kw in ['market', 'price', 'stock', 'value']):
            return RiskCategory.MARKET_PREDICTION

        # Check for valuations
        if any(kw in prediction_str for kw in ['valuation', 'worth', 'value']):
            return RiskCategory.COMPANY_VALUATION

        # Check for regulatory
        if any(kw in prediction_str for kw in ['compliance', 'regulation', 'legal']):
            return RiskCategory.REGULATORY_COMPLIANCE

        # Check for competitive
        if any(kw in prediction_str for kw in ['competitor', 'competitive', 'market share']):
            return RiskCategory.COMPETITIVE_ANALYSIS

        return RiskCategory.GENERAL_ANALYSIS

    def _calculate_risk_score(
        self,
        prediction: Any,
        context: Dict[str, Any],
        risk_category: RiskCategory
    ) -> float:
        """Calculate numerical risk score (0-1)."""
        base_scores = {
            RiskCategory.FINANCIAL_FORECAST: 0.8,
            RiskCategory.MARKET_PREDICTION: 0.85,
            RiskCategory.COMPANY_VALUATION: 0.75,
            RiskCategory.REGULATORY_COMPLIANCE: 0.9,
            RiskCategory.COMPETITIVE_ANALYSIS: 0.6,
            RiskCategory.GENERAL_ANALYSIS: 0.4
        }

        risk_score = base_scores.get(risk_category, 0.5)

        # Adjust based on context
        if context.get('uncertainty_high', False):
            risk_score += 0.1

        if context.get('historical_volatility', 0) > 0.5:
            risk_score += 0.05

        return min(risk_score, 1.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score."""
        if risk_score >= 0.85:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            return RiskLevel.HIGH
        elif risk_score >= 0.5:
            return RiskLevel.MODERATE
        elif risk_score >= 0.3:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL

    def _identify_risk_factors(
        self,
        prediction: Any,
        context: Dict[str, Any],
        risk_category: RiskCategory
    ) -> List[str]:
        """Identify specific risk factors."""
        factors = []

        if risk_category in [RiskCategory.FINANCIAL_FORECAST, RiskCategory.MARKET_PREDICTION]:
            factors.append("Forward-looking statement with inherent uncertainty")

        if context.get('data_quality', 1.0) < 0.8:
            factors.append("Data quality concerns")

        if context.get('sample_size', float('inf')) < 100:
            factors.append("Limited sample size")

        if context.get('time_horizon', 0) > 365:
            factors.append("Long-term prediction with increased uncertainty")

        return factors or ["Standard analytical uncertainty"]

    def _generate_mitigation_strategies(
        self,
        risk_level: RiskLevel,
        risk_category: RiskCategory,
        factors: List[str]
    ) -> List[str]:
        """Generate risk mitigation strategies."""
        strategies = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            strategies.append("Add prominent disclaimer about prediction uncertainty")
            strategies.append("Require additional expert review before publication")

        if risk_category == RiskCategory.FINANCIAL_FORECAST:
            strategies.append("Include confidence intervals and scenario analysis")

        if risk_category == RiskCategory.MARKET_PREDICTION:
            strategies.append("Emphasize historical volatility and external factors")

        if "data quality" in str(factors).lower():
            strategies.append("Supplement with additional data sources")

        strategies.append("Monitor prediction accuracy for continuous improvement")

        return strategies

    # Confidence Scoring Methods

    def _extract_model_scores(
        self,
        model_outputs: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract confidence scores from model outputs."""
        scores = {}

        for model, output in model_outputs.items():
            if isinstance(output, dict) and 'confidence' in output:
                scores[model] = output['confidence']
            elif isinstance(output, (int, float)):
                scores[model] = float(output)
            else:
                scores[model] = 0.7  # Default confidence

        return scores

    def _calculate_overall_confidence(
        self,
        model_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted overall confidence."""
        if not model_scores:
            return 0.5

        # Equal weighting for now (can be made configurable)
        return sum(model_scores.values()) / len(model_scores)

    def _calculate_agreement_level(
        self,
        model_outputs: Dict[str, Any]
    ) -> float:
        """Calculate agreement level between models."""
        if len(model_outputs) < 2:
            return 1.0

        # Simplified agreement calculation
        # In practice, would compare actual predictions
        scores = list(self._extract_model_scores(model_outputs).values())
        if not scores:
            return 0.5

        mean_score = sum(scores) / len(scores)
        deviations = [abs(s - mean_score) for s in scores]
        avg_deviation = sum(deviations) / len(deviations)

        # Convert to agreement (lower deviation = higher agreement)
        agreement = 1.0 - min(avg_deviation * 2, 1.0)
        return agreement

    def _calculate_variance(self, model_outputs: Dict[str, Any]) -> float:
        """Calculate variance in model predictions."""
        scores = list(self._extract_model_scores(model_outputs).values())
        if len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return variance

    # Prediction Adjustment Methods

    def _calculate_adjustment_factor(
        self,
        risk_assessment: RiskAssessment,
        confidence_score: ConfidenceScore
    ) -> float:
        """Calculate adjustment factor based on risk and confidence."""
        # Start with neutral adjustment
        adjustment = 1.0

        # Adjust based on risk level
        risk_adjustments = {
            RiskLevel.CRITICAL: 0.6,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MODERATE: 0.9,
            RiskLevel.LOW: 0.95,
            RiskLevel.MINIMAL: 1.0
        }
        adjustment *= risk_adjustments.get(risk_assessment.risk_level, 0.9)

        # Adjust based on confidence
        adjustment *= confidence_score.overall_confidence

        # Adjust based on model agreement
        adjustment *= confidence_score.agreement_level

        return adjustment

    def _apply_adjustment(
        self,
        prediction: Any,
        adjustment_factor: float,
        risk_assessment: RiskAssessment
    ) -> Any:
        """Apply adjustment to prediction."""
        # If prediction is numerical, scale it
        if isinstance(prediction, (int, float)):
            return prediction * adjustment_factor

        # If prediction is a dict with numerical values
        if isinstance(prediction, dict):
            adjusted = {}
            for key, value in prediction.items():
                if isinstance(value, (int, float)):
                    adjusted[key] = value * adjustment_factor
                else:
                    adjusted[key] = value

            # Add disclaimers
            adjusted['_goalie_disclaimer'] = self._generate_disclaimer(risk_assessment)
            return adjusted

        # For other types, return with metadata
        return {
            'prediction': prediction,
            'adjustment_factor': adjustment_factor,
            '_goalie_disclaimer': self._generate_disclaimer(risk_assessment)
        }

    def _generate_disclaimer(self, risk_assessment: RiskAssessment) -> str:
        """Generate appropriate disclaimer based on risk."""
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            return ("⚠️ CRITICAL: This prediction involves high uncertainty. "
                   "Seek professional advice before making decisions.")
        elif risk_assessment.risk_level == RiskLevel.HIGH:
            return ("⚠️ This prediction should be treated as indicative only. "
                   "Multiple factors may affect actual outcomes.")
        elif risk_assessment.risk_level == RiskLevel.MODERATE:
            return ("Note: This analysis contains forward-looking elements "
                   "subject to various uncertainties.")
        return "Standard analytical assumptions apply."

    def _generate_explanation(
        self,
        risk_assessment: RiskAssessment,
        confidence_score: ConfidenceScore,
        adjustment_factor: float
    ) -> str:
        """Generate explanation for adjustment."""
        explanation_parts = []

        explanation_parts.append(
            f"Risk Level: {risk_assessment.risk_level.value} "
            f"(score: {risk_assessment.risk_score:.2f})"
        )

        explanation_parts.append(
            f"Confidence: {confidence_score.overall_confidence:.2f} "
            f"(agreement: {confidence_score.agreement_level:.2f})"
        )

        if adjustment_factor < 0.9:
            explanation_parts.append(
                f"Prediction adjusted by {(1-adjustment_factor)*100:.1f}% "
                f"for risk mitigation"
            )

        if risk_assessment.mitigation_strategies:
            explanation_parts.append(
                f"Recommended: {risk_assessment.mitigation_strategies[0]}"
            )

        return " | ".join(explanation_parts)

    def _should_display(
        self,
        risk_assessment: RiskAssessment,
        confidence_score: ConfidenceScore
    ) -> bool:
        """Determine if prediction should be displayed."""
        # Don't display critical risk with low confidence
        if (risk_assessment.risk_level == RiskLevel.CRITICAL and
            confidence_score.overall_confidence < 0.6):
            return False

        # Don't display unreliable predictions
        if not confidence_score.reliable:
            return False

        # Don't display if variance is too high
        if confidence_score.variance > 0.3:
            return False

        return True

"""
Validation Metrics System

This module provides comprehensive metrics and thresholds for validation
quality assessment and monitoring.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    confidence_calibration: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ThresholdConfig:
    """Configuration for validation thresholds."""
    min_accuracy: float = 0.85
    min_precision: float = 0.80
    min_recall: float = 0.75
    max_false_positive_rate: float = 0.10
    max_false_negative_rate: float = 0.15
    min_confidence: float = 0.80
    min_model_agreement: float = 0.75


class MetricsCalculator:
    """Calculator for validation metrics."""

    def __init__(self, config: Optional[ThresholdConfig] = None):
        """Initialize metrics calculator."""
        self.config = config or ThresholdConfig()
        self.logger = logging.getLogger(__name__)

    def calculate_metrics(
        self,
        predictions: List[bool],
        actuals: List[bool],
        confidences: List[float]
    ) -> ValidationMetrics:
        """
        Calculate comprehensive validation metrics.

        Args:
            predictions: List of predicted values (True/False)
            actuals: List of actual values (True/False)
            confidences: List of confidence scores

        Returns:
            ValidationMetrics with all calculated metrics
        """
        if len(predictions) != len(actuals) or len(predictions) != len(confidences):
            raise ValueError("All input lists must have the same length")

        # Calculate confusion matrix elements
        tp = sum(1 for p, a in zip(predictions, actuals) if p and a)
        fp = sum(1 for p, a in zip(predictions, actuals) if p and not a)
        tn = sum(1 for p, a in zip(predictions, actuals) if not p and not a)
        fn = sum(1 for p, a in zip(predictions, actuals) if not p and a)

        # Calculate metrics
        total = len(predictions)
        accuracy = (tp + tn) / total if total > 0 else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )

        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # Calculate confidence calibration
        confidence_calibration = self._calculate_calibration(
            predictions,
            actuals,
            confidences
        )

        return ValidationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            confidence_calibration=confidence_calibration
        )

    def meets_thresholds(self, metrics: ValidationMetrics) -> bool:
        """Check if metrics meet configured thresholds."""
        return (
            metrics.accuracy >= self.config.min_accuracy and
            metrics.precision >= self.config.min_precision and
            metrics.recall >= self.config.min_recall and
            metrics.false_positive_rate <= self.config.max_false_positive_rate and
            metrics.false_negative_rate <= self.config.max_false_negative_rate
        )

    def _calculate_calibration(
        self,
        predictions: List[bool],
        actuals: List[bool],
        confidences: List[float]
    ) -> float:
        """
        Calculate confidence calibration score.

        A well-calibrated model should have accuracy match confidence.
        Returns a score between 0 (poor) and 1 (perfect).
        """
        if not confidences:
            return 0.0

        # Bin predictions by confidence level
        bins = [0.0, 0.5, 0.7, 0.8, 0.9, 1.0]
        bin_accuracies = []
        bin_confidences = []

        for i in range(len(bins) - 1):
            lower, upper = bins[i], bins[i + 1]

            # Get predictions in this bin
            bin_mask = [lower <= c < upper for c in confidences]
            bin_preds = [p for p, m in zip(predictions, bin_mask) if m]
            bin_acts = [a for a, m in zip(actuals, bin_mask) if m]
            bin_confs = [c for c, m in zip(confidences, bin_mask) if m]

            if bin_preds:
                # Calculate accuracy in bin
                bin_acc = sum(1 for p, a in zip(bin_preds, bin_acts) if p == a) / len(bin_preds)
                bin_avg_conf = sum(bin_confs) / len(bin_confs)

                bin_accuracies.append(bin_acc)
                bin_confidences.append(bin_avg_conf)

        # Calculate calibration error (lower is better)
        if bin_accuracies:
            calibration_error = sum(
                abs(acc - conf)
                for acc, conf in zip(bin_accuracies, bin_confidences)
            ) / len(bin_accuracies)

            # Convert to calibration score (higher is better)
            calibration_score = 1.0 - calibration_error
            return max(0.0, min(1.0, calibration_score))

        return 0.0


class MetricsTracker:
    """Track validation metrics over time."""

    def __init__(self):
        """Initialize metrics tracker."""
        self.history: List[ValidationMetrics] = []
        self.logger = logging.getLogger(__name__)

    def add_metrics(self, metrics: ValidationMetrics):
        """Add metrics to history."""
        self.history.append(metrics)
        self.logger.info(f"Added metrics: accuracy={metrics.accuracy:.3f}")

    def get_trend(self, metric_name: str, window: int = 10) -> List[float]:
        """Get trend for a specific metric."""
        if not self.history:
            return []

        recent = self.history[-window:]
        return [getattr(m, metric_name) for m in recent]

    def get_average(self, metric_name: str, window: int = 10) -> float:
        """Get average for a specific metric."""
        trend = self.get_trend(metric_name, window)
        return sum(trend) / len(trend) if trend else 0.0

    def is_degrading(self, metric_name: str, threshold: float = 0.05) -> bool:
        """Check if metric is degrading."""
        trend = self.get_trend(metric_name, window=5)
        if len(trend) < 2:
            return False

        # Check if there's a significant decline
        first_half = sum(trend[:len(trend)//2]) / (len(trend)//2)
        second_half = sum(trend[len(trend)//2:]) / (len(trend) - len(trend)//2)

        return (first_half - second_half) > threshold

    def export_metrics(self, filepath: str):
        """Export metrics history to JSON file."""
        data = [
            {
                'timestamp': m.timestamp,
                'accuracy': m.accuracy,
                'precision': m.precision,
                'recall': m.recall,
                'f1_score': m.f1_score,
                'false_positive_rate': m.false_positive_rate,
                'false_negative_rate': m.false_negative_rate,
                'confidence_calibration': m.confidence_calibration
            }
            for m in self.history
        ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported {len(data)} metrics to {filepath}")

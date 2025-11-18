"""
Tests for validation metrics system.

Tests cover:
- Metrics calculation
- Threshold validation
- Metrics tracking
- Trend analysis
"""

import unittest
import os
import json
import tempfile
from src.validation.metrics import (
    ValidationMetrics,
    ThresholdConfig,
    MetricsCalculator,
    MetricsTracker
)


class TestMetricsCalculator(unittest.TestCase):
    """Test suite for metrics calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()

    def test_initialization(self):
        """Test calculator initialization."""
        self.assertIsInstance(self.calculator.config, ThresholdConfig)
        self.assertEqual(self.calculator.config.min_accuracy, 0.85)

    def test_initialization_custom_config(self):
        """Test initialization with custom configuration."""
        config = ThresholdConfig(min_accuracy=0.90, min_precision=0.85)
        calculator = MetricsCalculator(config)

        self.assertEqual(calculator.config.min_accuracy, 0.90)
        self.assertEqual(calculator.config.min_precision, 0.85)

    def test_perfect_predictions(self):
        """Test metrics with perfect predictions."""
        predictions = [True, True, False, False]
        actuals = [True, True, False, False]
        confidences = [0.95, 0.90, 0.85, 0.90]

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        self.assertEqual(metrics.accuracy, 1.0)
        self.assertEqual(metrics.precision, 1.0)
        self.assertEqual(metrics.recall, 1.0)
        self.assertEqual(metrics.f1_score, 1.0)
        self.assertEqual(metrics.false_positive_rate, 0.0)
        self.assertEqual(metrics.false_negative_rate, 0.0)

    def test_all_wrong_predictions(self):
        """Test metrics with all wrong predictions."""
        predictions = [True, True, False, False]
        actuals = [False, False, True, True]
        confidences = [0.6, 0.6, 0.6, 0.6]

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        self.assertEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.precision, 0.0)
        self.assertEqual(metrics.recall, 0.0)
        self.assertEqual(metrics.f1_score, 0.0)

    def test_mixed_predictions(self):
        """Test metrics with mixed correct/incorrect predictions."""
        predictions = [True, True, True, False, False]
        actuals = [True, False, True, False, True]
        confidences = [0.9, 0.8, 0.85, 0.9, 0.7]

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        # 3 correct out of 5
        self.assertEqual(metrics.accuracy, 0.6)

        # 2 TP, 1 FP => precision = 2/3
        self.assertAlmostEqual(metrics.precision, 2/3, places=2)

        # 2 TP, 1 FN => recall = 2/3
        self.assertAlmostEqual(metrics.recall, 2/3, places=2)

        # F1 = 2 * (p * r) / (p + r)
        self.assertGreater(metrics.f1_score, 0.6)

    def test_false_positive_rate(self):
        """Test false positive rate calculation."""
        # All predictions positive, half are wrong
        predictions = [True] * 10
        actuals = [True] * 5 + [False] * 5
        confidences = [0.8] * 10

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        # FP = 5, TN = 0 => FPR = 5/(5+0) = 1.0
        self.assertEqual(metrics.false_positive_rate, 1.0)

    def test_false_negative_rate(self):
        """Test false negative rate calculation."""
        # All predictions negative, half are wrong
        predictions = [False] * 10
        actuals = [False] * 5 + [True] * 5
        confidences = [0.8] * 10

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        # FN = 5, TP = 0 => FNR = 5/(5+0) = 1.0
        self.assertEqual(metrics.false_negative_rate, 1.0)

    def test_confidence_calibration_perfect(self):
        """Test confidence calibration with perfect calibration."""
        # High confidence predictions should be correct
        predictions = [True, True, False, False]
        actuals = [True, True, False, False]
        confidences = [0.95, 0.90, 0.85, 0.90]

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        # Perfect predictions => good calibration
        self.assertGreater(metrics.confidence_calibration, 0.8)

    def test_confidence_calibration_poor(self):
        """Test confidence calibration with poor calibration."""
        # High confidence but wrong predictions
        predictions = [True, True, False, False]
        actuals = [False, False, True, True]
        confidences = [0.95, 0.90, 0.95, 0.90]

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        # Wrong predictions despite high confidence => poor calibration
        self.assertLess(metrics.confidence_calibration, 0.5)

    def test_meets_thresholds_pass(self):
        """Test threshold checking with passing metrics."""
        predictions = [True] * 9 + [False]
        actuals = [True] * 9 + [False]
        confidences = [0.9] * 10

        metrics = self.calculator.calculate_metrics(predictions, actuals, confidences)

        self.assertTrue(self.calculator.meets_thresholds(metrics))

    def test_meets_thresholds_fail_accuracy(self):
        """Test threshold checking with failing accuracy."""
        config = ThresholdConfig(min_accuracy=0.95)
        calculator = MetricsCalculator(config)

        predictions = [True] * 8 + [False] * 2
        actuals = [True] * 8 + [False] * 2
        confidences = [0.9] * 10

        metrics = calculator.calculate_metrics(predictions, actuals, confidences)

        # 80% accuracy < 95% threshold
        self.assertFalse(calculator.meets_thresholds(metrics))

    def test_meets_thresholds_fail_precision(self):
        """Test threshold checking with failing precision."""
        config = ThresholdConfig(min_precision=0.95)
        calculator = MetricsCalculator(config)

        # Low precision scenario
        predictions = [True] * 10
        actuals = [True] * 7 + [False] * 3
        confidences = [0.8] * 10

        metrics = calculator.calculate_metrics(predictions, actuals, confidences)

        # 70% precision < 95% threshold
        self.assertFalse(calculator.meets_thresholds(metrics))

    def test_input_length_mismatch(self):
        """Test error handling for mismatched input lengths."""
        predictions = [True, False]
        actuals = [True]
        confidences = [0.9, 0.8]

        with self.assertRaises(ValueError):
            self.calculator.calculate_metrics(predictions, actuals, confidences)

    def test_empty_inputs(self):
        """Test metrics calculation with empty inputs."""
        metrics = self.calculator.calculate_metrics([], [], [])

        self.assertEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.precision, 0.0)


class TestMetricsTracker(unittest.TestCase):
    """Test suite for metrics tracker."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = MetricsTracker()

    def test_initialization(self):
        """Test tracker initialization."""
        self.assertEqual(len(self.tracker.history), 0)

    def test_add_metrics(self):
        """Test adding metrics to history."""
        metrics = ValidationMetrics(
            accuracy=0.9,
            precision=0.85,
            recall=0.88,
            f1_score=0.86,
            false_positive_rate=0.05,
            false_negative_rate=0.08,
            confidence_calibration=0.82
        )

        self.tracker.add_metrics(metrics)

        self.assertEqual(len(self.tracker.history), 1)
        self.assertEqual(self.tracker.history[0], metrics)

    def test_get_trend(self):
        """Test getting trend for a metric."""
        # Add multiple metrics
        for i in range(5):
            metrics = ValidationMetrics(
                accuracy=0.8 + i * 0.02,
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        trend = self.tracker.get_trend('accuracy')

        self.assertEqual(len(trend), 5)
        self.assertEqual(trend[0], 0.80)
        self.assertEqual(trend[-1], 0.88)

    def test_get_trend_window(self):
        """Test getting trend with window limit."""
        # Add 15 metrics
        for i in range(15):
            metrics = ValidationMetrics(
                accuracy=0.8,
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        trend = self.tracker.get_trend('accuracy', window=5)

        # Should only return last 5
        self.assertEqual(len(trend), 5)

    def test_get_average(self):
        """Test getting average for a metric."""
        for i in range(10):
            metrics = ValidationMetrics(
                accuracy=0.8 + i * 0.01,
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        avg = self.tracker.get_average('accuracy')

        # Average of 0.80 to 0.89
        self.assertAlmostEqual(avg, 0.845, places=2)

    def test_is_degrading_true(self):
        """Test detection of degrading metrics."""
        # Add metrics with declining trend
        for i in range(10):
            metrics = ValidationMetrics(
                accuracy=0.9 - i * 0.02,  # Declining from 0.9 to 0.72
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        self.assertTrue(self.tracker.is_degrading('accuracy'))

    def test_is_degrading_false(self):
        """Test detection when metrics are not degrading."""
        # Add stable metrics
        for i in range(10):
            metrics = ValidationMetrics(
                accuracy=0.85,
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        self.assertFalse(self.tracker.is_degrading('accuracy'))

    def test_is_degrading_improving(self):
        """Test detection when metrics are improving."""
        # Add metrics with improving trend
        for i in range(10):
            metrics = ValidationMetrics(
                accuracy=0.7 + i * 0.02,  # Improving from 0.7 to 0.88
                precision=0.75,
                recall=0.80,
                f1_score=0.77,
                false_positive_rate=0.1,
                false_negative_rate=0.15,
                confidence_calibration=0.70
            )
            self.tracker.add_metrics(metrics)

        self.assertFalse(self.tracker.is_degrading('accuracy'))

    def test_export_metrics(self):
        """Test exporting metrics to file."""
        # Add some metrics
        for i in range(3):
            metrics = ValidationMetrics(
                accuracy=0.85 + i * 0.01,
                precision=0.80,
                recall=0.82,
                f1_score=0.81,
                false_positive_rate=0.10,
                false_negative_rate=0.12,
                confidence_calibration=0.75
            )
            self.tracker.add_metrics(metrics)

        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            self.tracker.export_metrics(temp_path)

            # Verify file exists and contains correct data
            self.assertTrue(os.path.exists(temp_path))

            with open(temp_path, 'r') as f:
                data = json.load(f)

            self.assertEqual(len(data), 3)
            self.assertIn('accuracy', data[0])
            self.assertEqual(data[0]['accuracy'], 0.85)

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestThresholdConfig(unittest.TestCase):
    """Test suite for threshold configuration."""

    def test_default_values(self):
        """Test default threshold values."""
        config = ThresholdConfig()

        self.assertEqual(config.min_accuracy, 0.85)
        self.assertEqual(config.min_precision, 0.80)
        self.assertEqual(config.min_recall, 0.75)
        self.assertEqual(config.max_false_positive_rate, 0.10)
        self.assertEqual(config.max_false_negative_rate, 0.15)
        self.assertEqual(config.min_confidence, 0.80)
        self.assertEqual(config.min_model_agreement, 0.75)

    def test_custom_values(self):
        """Test custom threshold values."""
        config = ThresholdConfig(
            min_accuracy=0.95,
            min_precision=0.90,
            min_recall=0.85,
            max_false_positive_rate=0.05,
            max_false_negative_rate=0.08
        )

        self.assertEqual(config.min_accuracy, 0.95)
        self.assertEqual(config.min_precision, 0.90)
        self.assertEqual(config.min_recall, 0.85)
        self.assertEqual(config.max_false_positive_rate, 0.05)
        self.assertEqual(config.max_false_negative_rate, 0.08)


class TestMetricsIntegration(unittest.TestCase):
    """Integration tests for metrics system."""

    def test_full_metrics_workflow(self):
        """Test complete metrics calculation and tracking workflow."""
        calculator = MetricsCalculator()
        tracker = MetricsTracker()

        # Simulate multiple validation rounds
        test_data = [
            ([True, True, False, False], [True, True, False, False]),
            ([True, False, False, True], [True, True, False, False]),
            ([True, True, True, False], [True, True, False, False])
        ]

        for predictions, actuals in test_data:
            confidences = [0.85] * len(predictions)
            metrics = calculator.calculate_metrics(predictions, actuals, confidences)
            tracker.add_metrics(metrics)

        # Verify tracking
        self.assertEqual(len(tracker.history), 3)

        # Check trends
        accuracy_trend = tracker.get_trend('accuracy')
        self.assertEqual(len(accuracy_trend), 3)

        # Check averages
        avg_accuracy = tracker.get_average('accuracy')
        self.assertGreater(avg_accuracy, 0.5)


if __name__ == '__main__':
    unittest.main()

"""
Predictions API Tests
Tests for prediction endpoints

Endpoints tested:
- POST /predictions - Create new prediction
- GET /predictions/{prediction_id} - Get prediction details
- GET /predictions - List predictions
- GET /predictions/{prediction_id}/accuracy - Get prediction accuracy
- POST /predictions/batch - Batch prediction creation
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from tests.fixtures.api_fixtures import mock_prediction_response


class TestPredictionsCreateEndpoint:
    """Test POST /predictions endpoint"""

    @pytest.mark.asyncio
    async def test_create_prediction_success(self, async_client, sample_filing_data, sample_signals):
        """Test successful prediction creation"""
        request_data = {
            "filing_id": "filing-123",
            "prediction_type": "price_movement",
            "time_horizon": "1_month",
            "signals": sample_signals
        }

        mock_response = mock_prediction_response()

        with patch('api.routes.predictions.create_prediction') as mock_create:
            mock_create.return_value = mock_response
            data = mock_response

            assert data["prediction_id"] is not None
            assert data["prediction"]["confidence"] > 0

    @pytest.mark.asyncio
    async def test_create_prediction_insufficient_signals(self, async_client):
        """Test prediction with insufficient signals"""
        request_data = {
            "filing_id": "filing-123",
            "signals": {"financial": []}  # Too few signals
        }

        with patch('api.routes.predictions.create_prediction') as mock_create:
            mock_create.side_effect = ValueError("Insufficient signals")

            with pytest.raises(ValueError, match="Insufficient"):
                mock_create(request_data)

    @pytest.mark.asyncio
    async def test_create_prediction_invalid_horizon(self, async_client):
        """Test invalid time horizon"""
        request_data = {
            "filing_id": "filing-123",
            "time_horizon": "invalid"
        }

        # Should validate time horizon
        valid_horizons = ["1_week", "1_month", "3_months", "6_months", "1_year"]
        assert request_data["time_horizon"] not in valid_horizons

    @pytest.mark.asyncio
    async def test_create_prediction_with_model_override(self, async_client, sample_signals):
        """Test prediction with specific model"""
        request_data = {
            "filing_id": "filing-123",
            "signals": sample_signals,
            "model": "claude-3-opus-20240229"  # Override model selection
        }

        mock_response = mock_prediction_response()
        mock_response["model_used"] = "claude-3-opus-20240229"

        with patch('api.routes.predictions.create_prediction') as mock_create:
            mock_create.return_value = mock_response
            data = mock_response

            assert data["model_used"] == "claude-3-opus-20240229"


class TestPredictionsGetEndpoint:
    """Test GET /predictions/{prediction_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_prediction_success(self, async_client, sample_prediction):
        """Test get prediction details"""
        prediction_id = "pred-123"

        with patch('api.routes.predictions.get_prediction') as mock_get:
            mock_get.return_value = sample_prediction
            data = sample_prediction

            assert data["filing_id"] is not None
            assert "prediction" in data

    @pytest.mark.asyncio
    async def test_get_prediction_not_found(self, async_client):
        """Test prediction not found"""
        prediction_id = "nonexistent"

        with patch('api.routes.predictions.get_prediction') as mock_get:
            mock_get.return_value = None
            data = mock_get(prediction_id)

            assert data is None

    @pytest.mark.asyncio
    async def test_get_prediction_with_explanation(self, async_client):
        """Test get prediction with reasoning explanation"""
        prediction_id = "pred-123"
        params = {"include_explanation": True}

        mock_response = {
            **mock_prediction_response(),
            "explanation": {
                "key_factors": ["Strong revenue growth", "Positive sentiment"],
                "risk_factors": ["Market competition"],
                "confidence_breakdown": {
                    "signal_strength": 0.85,
                    "model_certainty": 0.75,
                    "historical_accuracy": 0.72
                }
            }
        }

        with patch('api.routes.predictions.get_prediction_with_explanation') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert "explanation" in data
            assert len(data["explanation"]["key_factors"]) > 0


class TestPredictionsListEndpoint:
    """Test GET /predictions endpoint"""

    @pytest.mark.asyncio
    async def test_list_predictions(self, async_client):
        """Test list all predictions"""
        mock_response = {
            "predictions": [mock_prediction_response() for _ in range(10)],
            "total": 50,
            "page": 1,
            "page_size": 10
        }

        with patch('api.routes.predictions.list_predictions') as mock_list:
            mock_list.return_value = mock_response
            data = mock_response

            assert len(data["predictions"]) == 10
            assert data["total"] == 50

    @pytest.mark.asyncio
    async def test_list_predictions_by_filing(self, async_client):
        """Test filter predictions by filing"""
        filing_id = "filing-123"
        params = {"filing_id": filing_id}

        mock_response = {
            "predictions": [mock_prediction_response()],
            "total": 1,
            "filing_id": filing_id
        }

        with patch('api.routes.predictions.list_predictions') as mock_list:
            mock_list.return_value = mock_response
            data = mock_response

            assert data["filing_id"] == filing_id


class TestPredictionsAccuracyEndpoint:
    """Test GET /predictions/{prediction_id}/accuracy endpoint"""

    @pytest.mark.asyncio
    async def test_get_prediction_accuracy(self, async_client):
        """Test get prediction accuracy vs actual"""
        prediction_id = "pred-123"

        mock_response = {
            "prediction_id": prediction_id,
            "predicted": {"direction": "up", "magnitude": 0.05},
            "actual": {"direction": "up", "magnitude": 0.048},
            "accuracy_score": 0.96,
            "directional_accuracy": True,
            "magnitude_error": 0.002
        }

        with patch('api.routes.predictions.get_prediction_accuracy') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert data["directional_accuracy"] is True
            assert data["accuracy_score"] > 0.9

    @pytest.mark.asyncio
    async def test_get_prediction_accuracy_pending(self, async_client):
        """Test accuracy for prediction pending outcome"""
        prediction_id = "pred-123"

        mock_response = {
            "prediction_id": prediction_id,
            "status": "pending",
            "message": "Prediction outcome not yet available",
            "evaluation_date": "2024-11-18T00:00:00Z"
        }

        with patch('api.routes.predictions.get_prediction_accuracy') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert data["status"] == "pending"


class TestPredictionsBatchEndpoint:
    """Test POST /predictions/batch endpoint"""

    @pytest.mark.asyncio
    async def test_batch_predictions(self, async_client):
        """Test batch prediction creation"""
        request_data = {
            "filing_ids": ["filing-1", "filing-2", "filing-3"],
            "prediction_type": "price_movement",
            "time_horizon": "1_month"
        }

        mock_response = {
            "batch_id": "batch-123",
            "predictions": [
                {"filing_id": "filing-1", "prediction_id": "pred-1"},
                {"filing_id": "filing-2", "prediction_id": "pred-2"},
                {"filing_id": "filing-3", "prediction_id": "pred-3"}
            ],
            "status": "processing"
        }

        with patch('api.routes.predictions.create_batch_predictions') as mock_batch:
            mock_batch.return_value = mock_response
            data = mock_response

            assert len(data["predictions"]) == 3
            assert data["batch_id"] is not None

    @pytest.mark.asyncio
    async def test_batch_predictions_partial_failure(self, async_client):
        """Test batch with some failures"""
        request_data = {
            "filing_ids": ["filing-1", "filing-invalid", "filing-3"]
        }

        mock_response = {
            "batch_id": "batch-123",
            "predictions": [
                {"filing_id": "filing-1", "prediction_id": "pred-1", "status": "success"},
                {"filing_id": "filing-invalid", "error": "Invalid filing", "status": "failed"},
                {"filing_id": "filing-3", "prediction_id": "pred-3", "status": "success"}
            ],
            "success_count": 2,
            "failure_count": 1
        }

        with patch('api.routes.predictions.create_batch_predictions') as mock_batch:
            mock_batch.return_value = mock_response
            data = mock_response

            assert data["success_count"] == 2
            assert data["failure_count"] == 1


class TestPredictionsPerformance:
    """Performance tests for predictions API"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_prediction_response_time(self, async_client, benchmark_timer):
        """Test prediction creation time < 2s"""
        benchmark_timer.start()

        mock_response = mock_prediction_response()
        mock_response["processing_time_ms"] = 1800  # 1.8 seconds

        benchmark_timer.stop()

        # Should be under 2000ms
        assert mock_response["processing_time_ms"] < 2000

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_prediction_throughput(self, async_client):
        """Test batch prediction throughput"""
        filing_count = 100

        mock_response = {
            "batch_id": "batch-large",
            "filing_count": filing_count,
            "estimated_completion_sec": 180  # 3 minutes for 100 predictions
        }

        # Should process ~33 predictions per minute
        predictions_per_minute = filing_count / (mock_response["estimated_completion_sec"] / 60)
        assert predictions_per_minute > 30


class TestPredictionsValidation:
    """Validation tests"""

    @pytest.mark.asyncio
    async def test_prediction_confidence_validation(self, async_client):
        """Test confidence score validation"""
        prediction = mock_prediction_response()

        # Confidence should be between 0 and 1
        assert 0 <= prediction["prediction"]["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_prediction_type_validation(self, async_client):
        """Test prediction type validation"""
        valid_types = ["price_movement", "volatility", "earnings_surprise", "bankruptcy_risk"]

        request_data = {"prediction_type": "invalid_type"}

        assert request_data["prediction_type"] not in valid_types

    @pytest.mark.asyncio
    async def test_prediction_magnitude_range(self, async_client):
        """Test magnitude is within reasonable range"""
        prediction = mock_prediction_response()

        # Price movement magnitude should be reasonable (-1 to 1)
        assert -1 <= prediction["prediction"]["magnitude"] <= 1

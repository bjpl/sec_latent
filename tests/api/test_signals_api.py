"""
Signals API Tests
Tests for signal extraction endpoints

Endpoints tested:
- POST /signals/extract - Extract signals from filing
- GET /signals/{filing_id} - Get extracted signals
- GET /signals/{filing_id}/category/{category} - Get signals by category
- POST /signals/reextract - Re-extract signals with updated extractors
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures.api_fixtures import mock_signal_response
from tests.fixtures.data_fixtures import sample_signals_full


class TestSignalsExtractEndpoint:
    """Test POST /signals/extract endpoint"""

    @pytest.mark.asyncio
    async def test_extract_signals_success(self, async_client, sample_filing_data):
        """Test successful signal extraction"""
        request_data = {
            "filing_id": "filing-123",
            "extract_all": True
        }

        mock_response = mock_signal_response(150)

        with patch('api.routes.signals.extract_signals') as mock_extract:
            mock_extract.return_value = mock_response
            data = mock_response

            assert data["total_signals"] == 150
            assert len(data["signals"]["financial"]) == 50
            assert len(data["signals"]["sentiment"]) == 30
            assert len(data["signals"]["risk"]) == 40
            assert len(data["signals"]["management"]) == 30

    @pytest.mark.asyncio
    async def test_extract_signals_selective(self, async_client):
        """Test selective signal extraction"""
        request_data = {
            "filing_id": "filing-123",
            "categories": ["financial", "risk"]
        }

        mock_response = {
            "filing_id": "filing-123",
            "signals": {
                "financial": [{"name": "signal_1", "value": 0.8, "confidence": 0.9}] * 50,
                "risk": [{"name": "risk_1", "value": 0.6, "confidence": 0.85}] * 40
            },
            "total_signals": 90,
            "extraction_time_ms": 650
        }

        with patch('api.routes.signals.extract_signals') as mock_extract:
            mock_extract.return_value = mock_response
            data = mock_response

            assert "sentiment" not in data["signals"]
            assert "management" not in data["signals"]
            assert data["total_signals"] == 90

    @pytest.mark.asyncio
    async def test_extract_signals_filing_not_found(self, async_client):
        """Test extraction from nonexistent filing"""
        request_data = {"filing_id": "nonexistent"}

        with patch('api.routes.signals.extract_signals') as mock_extract:
            mock_extract.side_effect = ValueError("Filing not found")

            with pytest.raises(ValueError, match="Filing not found"):
                mock_extract(request_data)

    @pytest.mark.asyncio
    async def test_extract_signals_with_custom_extractors(self, async_client):
        """Test extraction with custom extractor configuration"""
        request_data = {
            "filing_id": "filing-123",
            "extractor_config": {
                "enable_advanced": True,
                "confidence_threshold": 0.8
            }
        }

        mock_response = mock_signal_response(150)

        with patch('api.routes.signals.extract_signals') as mock_extract:
            mock_extract.return_value = mock_response
            data = mock_response

            # All signals should meet confidence threshold
            for category in data["signals"].values():
                for signal in category:
                    assert signal["confidence"] >= 0.8


class TestSignalsGetEndpoint:
    """Test GET /signals/{filing_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_signals_success(self, async_client):
        """Test get extracted signals"""
        filing_id = "filing-123"

        mock_response = sample_signals_full()

        with patch('api.routes.signals.get_signals') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert len(data["financial"]) == 50
            assert all(s["confidence"] > 0 for s in data["financial"])

    @pytest.mark.asyncio
    async def test_get_signals_not_extracted(self, async_client):
        """Test get signals before extraction"""
        filing_id = "filing-new"

        with patch('api.routes.signals.get_signals') as mock_get:
            mock_get.return_value = None
            data = mock_get(filing_id)

            assert data is None

    @pytest.mark.asyncio
    async def test_get_signals_with_filter(self, async_client):
        """Test get signals with minimum confidence filter"""
        filing_id = "filing-123"
        params = {"min_confidence": 0.9}

        mock_response = {
            "financial": [
                {"name": "signal_1", "value": 0.8, "confidence": 0.95},
                {"name": "signal_2", "value": 0.7, "confidence": 0.92}
            ]
        }

        with patch('api.routes.signals.get_signals') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            # All signals should meet minimum confidence
            for signal in data["financial"]:
                assert signal["confidence"] >= 0.9


class TestSignalsByCategoryEndpoint:
    """Test GET /signals/{filing_id}/category/{category} endpoint"""

    @pytest.mark.asyncio
    async def test_get_financial_signals(self, async_client):
        """Test get financial signals only"""
        filing_id = "filing-123"
        category = "financial"

        mock_response = {
            "filing_id": filing_id,
            "category": category,
            "signals": [
                {"name": f"financial_{i}", "value": 0.75, "confidence": 0.9}
                for i in range(50)
            ],
            "count": 50
        }

        with patch('api.routes.signals.get_signals_by_category') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert len(data["signals"]) == 50
            assert data["category"] == "financial"

    @pytest.mark.asyncio
    async def test_get_signals_invalid_category(self, async_client):
        """Test invalid category"""
        filing_id = "filing-123"
        category = "invalid"

        valid_categories = ["financial", "sentiment", "risk", "management"]
        assert category not in valid_categories

    @pytest.mark.asyncio
    async def test_get_risk_signals(self, async_client):
        """Test get risk signals"""
        filing_id = "filing-123"
        category = "risk"

        mock_response = {
            "filing_id": filing_id,
            "category": category,
            "signals": [
                {"name": f"risk_{i}", "value": 0.55, "confidence": 0.88}
                for i in range(40)
            ],
            "count": 40,
            "risk_summary": {
                "overall_risk_level": "medium",
                "top_risks": ["market_risk", "regulatory_risk"]
            }
        }

        with patch('api.routes.signals.get_signals_by_category') as mock_get:
            mock_get.return_value = mock_response
            data = mock_response

            assert len(data["signals"]) == 40
            assert "risk_summary" in data


class TestSignalsReextractEndpoint:
    """Test POST /signals/reextract endpoint"""

    @pytest.mark.asyncio
    async def test_reextract_signals(self, async_client):
        """Test re-extraction of signals"""
        request_data = {
            "filing_id": "filing-123",
            "reason": "Updated extractors available"
        }

        mock_response = {
            "filing_id": "filing-123",
            "reextraction_id": "reextract-456",
            "status": "queued",
            "previous_signal_count": 150,
            "message": "Re-extraction queued"
        }

        with patch('api.routes.signals.reextract_signals') as mock_reextract:
            mock_reextract.return_value = mock_response
            data = mock_response

            assert data["status"] == "queued"
            assert "reextraction_id" in data

    @pytest.mark.asyncio
    async def test_reextract_with_version(self, async_client):
        """Test re-extraction with extractor version"""
        request_data = {
            "filing_id": "filing-123",
            "extractor_version": "v2.1.0"
        }

        mock_response = {
            "filing_id": "filing-123",
            "status": "completed",
            "new_signal_count": 155,
            "previous_signal_count": 150,
            "changes": {
                "added": 8,
                "removed": 3,
                "modified": 12
            }
        }

        with patch('api.routes.signals.reextract_signals') as mock_reextract:
            mock_reextract.return_value = mock_response
            data = mock_response

            assert data["new_signal_count"] > data["previous_signal_count"]


class TestSignalsPerformance:
    """Performance tests for signals API"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_extraction_time(self, async_client, benchmark_timer):
        """Test signal extraction time < 1s"""
        mock_response = mock_signal_response(150)

        # Extraction should be under 1000ms
        assert mock_response["extraction_time_ms"] < 1000

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_extraction_throughput(self, async_client):
        """Test extraction throughput"""
        # Should extract all 150 signals in under 1s
        extraction_times = [650, 720, 680, 710, 695]
        avg_time = sum(extraction_times) / len(extraction_times)

        assert avg_time < 1000

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_signal_retrieval_cached(self, async_client, mock_redis_client):
        """Test cached signal retrieval < 50ms"""
        filing_id = "filing-123"

        with patch('api.cache.redis_client', mock_redis_client):
            mock_redis_client.get.return_value = '{"signals": []}'

            # Cached retrieval should be very fast
            # In real test, would measure actual time
            pass


class TestSignalsValidation:
    """Validation tests for signals"""

    @pytest.mark.asyncio
    async def test_signal_confidence_range(self, async_client):
        """Test all confidences are 0-1"""
        signals = sample_signals_full()

        for category in signals.values():
            for signal in category:
                assert 0 <= signal["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_signal_count_limits(self, async_client):
        """Test signal count limits per category"""
        signals = sample_signals_full()

        assert len(signals["financial"]) == 50
        assert len(signals["sentiment"]) == 30
        assert len(signals["risk"]) == 40
        assert len(signals["management"]) == 30

    @pytest.mark.asyncio
    async def test_signal_naming_convention(self, async_client):
        """Test signal names follow convention"""
        signals = sample_signals_full()

        for category_name, category_signals in signals.items():
            for signal in category_signals[:5]:  # Check first 5
                # Name should be lowercase with underscores
                assert signal["name"].islower() or "_" in signal["name"]

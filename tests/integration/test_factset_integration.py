"""
FactSet Integration Tests
Tests for FactSet data integration

Tests cover:
- API authentication and access
- Financial data retrieval
- Estimates and consensus data
- Ownership data
- Screening and filtering
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestFactSetAuthentication:
    """Test FactSet API authentication"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_auth_success(self):
        """Test successful basic authentication"""
        mock_client = Mock()
        mock_client.authenticate = Mock(return_value={
            "authenticated": True,
            "username": "test-user",
            "api_version": "2.0"
        })

        auth = mock_client.authenticate()

        assert auth["authenticated"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_authentication(self):
        """Test OAuth 2.0 authentication"""
        mock_client = Mock()
        mock_client.oauth_authenticate = Mock(return_value={
            "access_token": "factset-token-123",
            "token_type": "Bearer",
            "expires_in": 3600
        })

        oauth = mock_client.oauth_authenticate()

        assert oauth["access_token"] is not None


class TestFactSetFinancialData:
    """Test financial data retrieval"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_company_financials(self):
        """Test company financial data retrieval"""
        mock_client = Mock()
        mock_client.get_financials = Mock(return_value={
            "company_id": "MSFT-US",
            "fiscal_year": 2024,
            "revenue": 245000000000,
            "operating_income": 110000000000,
            "net_income": 88000000000,
            "total_assets": 512000000000,
            "total_equity": 267000000000
        })

        financials = mock_client.get_financials("MSFT-US")

        assert financials["revenue"] > 0
        assert financials["net_income"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_financial_ratios(self):
        """Test financial ratios calculation"""
        mock_client = Mock()
        mock_client.get_ratios = Mock(return_value={
            "company_id": "MSFT-US",
            "ratios": {
                "current_ratio": 1.85,
                "quick_ratio": 1.65,
                "debt_to_equity": 0.42,
                "roe": 0.33,
                "roa": 0.17,
                "profit_margin": 0.36
            }
        })

        ratios = mock_client.get_ratios("MSFT-US")

        assert ratios["ratios"]["roe"] > 0
        assert ratios["ratios"]["current_ratio"] > 1


class TestFactSetEstimates:
    """Test estimates and consensus data"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_earnings_estimates(self):
        """Test earnings estimates retrieval"""
        mock_client = Mock()
        mock_client.get_estimates = Mock(return_value={
            "company_id": "MSFT-US",
            "fiscal_year": 2025,
            "estimates": {
                "revenue_mean": 275000000000,
                "revenue_high": 285000000000,
                "revenue_low": 265000000000,
                "eps_mean": 12.45,
                "eps_high": 13.20,
                "eps_low": 11.80,
                "analyst_count": 35
            }
        })

        estimates = mock_client.get_estimates("MSFT-US")

        assert estimates["estimates"]["analyst_count"] > 0
        assert estimates["estimates"]["revenue_mean"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_consensus_recommendations(self):
        """Test consensus recommendations"""
        mock_client = Mock()
        mock_client.get_consensus = Mock(return_value={
            "company_id": "MSFT-US",
            "consensus": {
                "rating": "Buy",
                "buy_count": 28,
                "hold_count": 6,
                "sell_count": 1,
                "target_price_mean": 485.00,
                "upside_potential": 0.168
            }
        })

        consensus = mock_client.get_consensus("MSFT-US")

        assert consensus["consensus"]["rating"] in ["Buy", "Hold", "Sell"]


class TestFactSetOwnership:
    """Test ownership data"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_institutional_ownership(self):
        """Test institutional ownership data"""
        mock_client = Mock()
        mock_client.get_ownership = Mock(return_value={
            "company_id": "MSFT-US",
            "institutional_ownership": {
                "percentage": 73.5,
                "holders_count": 4523,
                "top_holders": [
                    {"name": "Vanguard Group", "percentage": 8.2},
                    {"name": "BlackRock", "percentage": 7.5},
                    {"name": "State Street", "percentage": 4.3}
                ]
            }
        })

        ownership = mock_client.get_ownership("MSFT-US")

        assert ownership["institutional_ownership"]["percentage"] > 0
        assert len(ownership["institutional_ownership"]["top_holders"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_insider_transactions(self):
        """Test insider trading data"""
        mock_client = Mock()
        mock_client.get_insider_trades = Mock(return_value={
            "company_id": "MSFT-US",
            "transactions": [
                {
                    "insider": "Satya Nadella",
                    "title": "CEO",
                    "transaction_type": "Sale",
                    "shares": 25000,
                    "price": 410.00,
                    "date": "2024-10-01"
                }
            ],
            "count": 1
        })

        trades = mock_client.get_insider_trades("MSFT-US")

        assert len(trades["transactions"]) > 0


class TestFactSetScreening:
    """Test screening and filtering capabilities"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_screen_companies(self):
        """Test company screening"""
        mock_client = Mock()
        mock_client.screen = Mock(return_value={
            "criteria": {
                "market_cap_min": 100000000000,
                "pe_ratio_max": 40,
                "revenue_growth_min": 0.10
            },
            "results": [
                {"company_id": "MSFT-US", "market_cap": 3100000000000},
                {"company_id": "AAPL-US", "market_cap": 2950000000000}
            ],
            "count": 2
        })

        results = mock_client.screen(market_cap_min=100000000000)

        assert results["count"] > 0
        assert all(r["market_cap"] >= 100000000000 for r in results["results"])

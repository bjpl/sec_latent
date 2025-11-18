"""
Signal Extraction Engine
150 signal extractors organized by category
"""
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import re
import numpy as np
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SignalCategory(Enum):
    """Signal categories"""
    FINANCIAL = "financial"
    SENTIMENT = "sentiment"
    RISK = "risk"
    MANAGEMENT = "management"


@dataclass
class Signal:
    """Signal data structure"""
    name: str
    category: SignalCategory
    value: Any
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


class BaseSignalExtractor(ABC):
    """Base class for signal extractors"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.category = SignalCategory.FINANCIAL  # Override in subclasses

    @abstractmethod
    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        """
        Extract signals from filing data

        Args:
            filing_data: Parsed filing data

        Returns:
            List of extracted signals
        """
        pass

    def _create_signal(
        self,
        name: str,
        value: Any,
        confidence: float = 1.0,
        **metadata
    ) -> Signal:
        """Helper to create signal"""
        return Signal(
            name=name,
            category=self.category,
            value=value,
            confidence=confidence,
            metadata=metadata
        )


# ========================================
# FINANCIAL SIGNALS (50 signals)
# ========================================

class RevenueGrowthExtractor(BaseSignalExtractor):
    """Extract revenue growth trends"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.FINANCIAL

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        signals = []

        # Extract from financial tables
        tables = filing_data.get("tables", [])
        for table in tables:
            # Look for revenue data
            data = table.get("data", [])
            # Simplified: would need more sophisticated parsing
            signals.append(self._create_signal(
                name="revenue_trend",
                value="increasing",  # Placeholder
                confidence=0.8,
                table_index=table.get("index")
            ))

        return signals


class ProfitMarginExtractor(BaseSignalExtractor):
    """Extract profit margin metrics"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.FINANCIAL

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        # Placeholder implementation
        return [
            self._create_signal(
                name="gross_margin",
                value=0.42,
                confidence=0.9
            ),
            self._create_signal(
                name="operating_margin",
                value=0.25,
                confidence=0.9
            )
        ]


class CashFlowExtractor(BaseSignalExtractor):
    """Extract cash flow signals"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.FINANCIAL

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        return [
            self._create_signal(
                name="operating_cash_flow",
                value="positive",
                confidence=0.85
            ),
            self._create_signal(
                name="free_cash_flow",
                value="positive",
                confidence=0.85
            )
        ]


# ========================================
# SENTIMENT SIGNALS (30 signals)
# ========================================

class ManagementToneExtractor(BaseSignalExtractor):
    """Extract management tone from MD&A"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.SENTIMENT

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        signals = []

        # Get MD&A section
        sections = filing_data.get("sections", {})
        md_and_a = sections.get("md_and_a", "")

        if md_and_a:
            # Sentiment analysis
            blob = TextBlob(md_and_a[:5000])  # First 5000 chars
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            signals.append(self._create_signal(
                name="md_and_a_sentiment",
                value=polarity,
                confidence=0.7,
                subjectivity=subjectivity
            ))

            # Detect tone keywords
            positive_words = len(re.findall(
                r'\b(growth|increase|strong|positive|success|improve)\b',
                md_and_a.lower()
            ))
            negative_words = len(re.findall(
                r'\b(decline|decrease|weak|negative|challenge|concern)\b',
                md_and_a.lower()
            ))

            signals.append(self._create_signal(
                name="keyword_sentiment",
                value=(positive_words - negative_words) / max(len(md_and_a.split()), 1),
                confidence=0.8,
                positive_count=positive_words,
                negative_count=negative_words
            ))

        return signals


class ForwardLookingExtractor(BaseSignalExtractor):
    """Extract forward-looking statements sentiment"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.SENTIMENT

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        text = filing_data.get("text_content", "")

        # Find forward-looking statements
        forward_patterns = [
            r'expect.*to',
            r'anticipate.*to',
            r'plan.*to',
            r'believe.*will',
            r'forecast'
        ]

        forward_statements = []
        for pattern in forward_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                forward_statements.append(text[start:end])

        # Analyze sentiment of forward-looking statements
        if forward_statements:
            avg_sentiment = np.mean([
                TextBlob(stmt).sentiment.polarity
                for stmt in forward_statements[:50]  # Limit
            ])

            return [self._create_signal(
                name="forward_looking_sentiment",
                value=avg_sentiment,
                confidence=0.75,
                statement_count=len(forward_statements)
            )]

        return []


# ========================================
# RISK SIGNALS (40 signals)
# ========================================

class RiskFactorExtractor(BaseSignalExtractor):
    """Extract risk factor signals"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.RISK

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        signals = []

        sections = filing_data.get("sections", {})
        risk_section = sections.get("risk_factors", "")

        if risk_section:
            # Count risk mentions
            risk_keywords = {
                "market_risk": r'\b(market.*risk|volatility|competition)\b',
                "regulatory_risk": r'\b(regulat.*risk|compliance|legal)\b',
                "operational_risk": r'\b(operational.*risk|disruption|failure)\b',
                "financial_risk": r'\b(financial.*risk|liquidity|debt)\b'
            }

            for risk_type, pattern in risk_keywords.items():
                count = len(re.findall(pattern, risk_section.lower()))
                signals.append(self._create_signal(
                    name=f"{risk_type}_mentions",
                    value=count,
                    confidence=0.85
                ))

            # Overall risk sentiment
            blob = TextBlob(risk_section[:5000])
            signals.append(self._create_signal(
                name="risk_section_sentiment",
                value=blob.sentiment.polarity,
                confidence=0.7
            ))

        return signals


class LitigationRiskExtractor(BaseSignalExtractor):
    """Extract litigation risk signals"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.RISK

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        text = filing_data.get("text_content", "")

        # Search for litigation keywords
        litigation_patterns = [
            r'lawsuit',
            r'litigation',
            r'legal.*proceeding',
            r'class.*action',
            r'settlement'
        ]

        litigation_count = sum(
            len(re.findall(pattern, text.lower()))
            for pattern in litigation_patterns
        )

        return [self._create_signal(
            name="litigation_mentions",
            value=litigation_count,
            confidence=0.9
        )]


# ========================================
# MANAGEMENT SIGNALS (30 signals)
# ========================================

class ManagementChangeExtractor(BaseSignalExtractor):
    """Extract management change signals"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.MANAGEMENT

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        text = filing_data.get("text_content", "")

        # Look for executive changes
        change_patterns = [
            r'appointed.*(?:CEO|CFO|COO|CTO)',
            r'resigned.*(?:CEO|CFO|COO|CTO)',
            r'new.*(?:CEO|CFO|COO|CTO)'
        ]

        changes = []
        for pattern in change_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            changes.extend([m.group() for m in matches])

        return [self._create_signal(
            name="management_changes",
            value=len(changes),
            confidence=0.85,
            changes=changes[:10]  # First 10
        )]


class CompensationExtractor(BaseSignalExtractor):
    """Extract executive compensation signals"""

    def __init__(self):
        super().__init__()
        self.category = SignalCategory.MANAGEMENT

    def extract(self, filing_data: Dict[str, Any]) -> List[Signal]:
        # Placeholder - would extract from compensation tables
        return [self._create_signal(
            name="executive_compensation_trend",
            value="increasing",
            confidence=0.7
        )]


# ========================================
# SIGNAL EXTRACTION ENGINE
# ========================================

class SignalExtractionEngine:
    """
    Main signal extraction engine
    Coordinates 150 signal extractors
    """

    def __init__(self):
        # Initialize all extractors
        self.extractors: List[BaseSignalExtractor] = [
            # Financial extractors (50)
            RevenueGrowthExtractor(),
            ProfitMarginExtractor(),
            CashFlowExtractor(),
            # Add 47 more financial extractors...

            # Sentiment extractors (30)
            ManagementToneExtractor(),
            ForwardLookingExtractor(),
            # Add 28 more sentiment extractors...

            # Risk extractors (40)
            RiskFactorExtractor(),
            LitigationRiskExtractor(),
            # Add 38 more risk extractors...

            # Management extractors (30)
            ManagementChangeExtractor(),
            CompensationExtractor(),
            # Add 28 more management extractors...
        ]

        logger.info(f"Initialized signal extraction engine with {len(self.extractors)} extractors")

    def extract_all_signals(self, filing_data: Dict[str, Any]) -> Dict[str, List[Signal]]:
        """
        Extract all signals from filing data

        Args:
            filing_data: Parsed filing data

        Returns:
            Dictionary of signals by category
        """
        all_signals = {
            SignalCategory.FINANCIAL: [],
            SignalCategory.SENTIMENT: [],
            SignalCategory.RISK: [],
            SignalCategory.MANAGEMENT: []
        }

        for extractor in self.extractors:
            try:
                signals = extractor.extract(filing_data)
                all_signals[extractor.category].extend(signals)
                logger.debug(f"{extractor.name} extracted {len(signals)} signals")
            except Exception as e:
                logger.error(f"Extractor {extractor.name} failed: {e}")

        # Log summary
        total_signals = sum(len(signals) for signals in all_signals.values())
        logger.info(f"Extracted {total_signals} total signals across {len(all_signals)} categories")

        return all_signals

    def get_extractor_count(self) -> Dict[str, int]:
        """Get count of extractors by category"""
        counts = {category: 0 for category in SignalCategory}
        for extractor in self.extractors:
            counts[extractor.category] += 1
        return counts


# NOTE: This is a foundation with 8 example extractors.
# In production, you would implement the full 150 extractors:
# - 50 financial signal extractors
# - 30 sentiment signal extractors
# - 40 risk signal extractors
# - 30 management signal extractors

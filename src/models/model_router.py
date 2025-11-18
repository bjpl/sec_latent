"""
Model Router
Intelligent routing to appropriate Claude model based on complexity
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available Claude models"""
    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-opus-20240229"


class ComplexityLevel(Enum):
    """Task complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelRouter:
    """
    Routes tasks to appropriate Claude model based on complexity
    Implements retry logic and fallback mechanisms
    """

    def __init__(self):
        self.settings = get_settings().models
        self.clients = self._initialize_clients()

        # Routing thresholds
        self.complexity_thresholds = {
            ComplexityLevel.LOW: 0.0,
            ComplexityLevel.MEDIUM: self.settings.complexity_threshold_medium,
            ComplexityLevel.HIGH: self.settings.complexity_threshold_high
        }

    def _initialize_clients(self) -> Dict[ModelType, anthropic.Anthropic]:
        """Initialize API clients for each model"""
        clients = {}

        # Haiku client
        if self.settings.haiku_api_key:
            clients[ModelType.HAIKU] = anthropic.Anthropic(
                api_key=self.settings.haiku_api_key,
                base_url=self.settings.haiku_endpoint
            )

        # Sonnet client
        if self.settings.sonnet_api_key:
            clients[ModelType.SONNET] = anthropic.Anthropic(
                api_key=self.settings.sonnet_api_key,
                base_url=self.settings.sonnet_endpoint
            )

        # Opus client (optional)
        if self.settings.opus_api_key:
            clients[ModelType.OPUS] = anthropic.Anthropic(
                api_key=self.settings.opus_api_key,
                base_url=self.settings.opus_endpoint
            )

        logger.info(f"Initialized {len(clients)} model clients")
        return clients

    def assess_complexity(
        self,
        text: str,
        signal_count: int,
        filing_type: str,
        custom_factors: Optional[Dict[str, Any]] = None
    ) -> ComplexityLevel:
        """
        Assess task complexity to determine appropriate model

        Args:
            text: Input text to analyze
            signal_count: Number of signals to extract
            filing_type: Type of SEC filing (10-K, 10-Q, etc.)
            custom_factors: Additional complexity factors

        Returns:
            Complexity level
        """
        factors = []

        # Text length factor (0-1)
        text_length = len(text)
        length_factor = min(text_length / 50000, 1.0)  # Normalize to 50k chars
        factors.append(length_factor)

        # Signal count factor (0-1)
        signal_factor = min(signal_count / 150, 1.0)  # Normalize to 150 signals
        factors.append(signal_factor)

        # Filing type factor
        filing_complexity = {
            "10-K": 0.9,  # Annual report - high complexity
            "10-Q": 0.6,  # Quarterly report - medium
            "8-K": 0.3,   # Current report - low
            "DEF 14A": 0.7  # Proxy statement - medium-high
        }
        factors.append(filing_complexity.get(filing_type, 0.5))

        # Custom factors
        if custom_factors:
            if "table_count" in custom_factors:
                table_factor = min(custom_factors["table_count"] / 20, 1.0)
                factors.append(table_factor)

            if "section_count" in custom_factors:
                section_factor = min(custom_factors["section_count"] / 10, 1.0)
                factors.append(section_factor)

        # Calculate overall complexity score
        complexity_score = np.mean(factors)

        # Map to complexity level
        if complexity_score >= self.complexity_thresholds[ComplexityLevel.HIGH]:
            level = ComplexityLevel.HIGH
        elif complexity_score >= self.complexity_thresholds[ComplexityLevel.MEDIUM]:
            level = ComplexityLevel.MEDIUM
        else:
            level = ComplexityLevel.LOW

        logger.info(f"Assessed complexity: {level.value} (score: {complexity_score:.2f})")
        return level

    def select_model(self, complexity: ComplexityLevel) -> ModelType:
        """
        Select appropriate model based on complexity

        Args:
            complexity: Task complexity level

        Returns:
            Selected model type
        """
        model_map = {
            ComplexityLevel.LOW: ModelType.HAIKU,
            ComplexityLevel.MEDIUM: ModelType.SONNET,
            ComplexityLevel.HIGH: ModelType.OPUS if ModelType.OPUS in self.clients else ModelType.SONNET
        }

        selected = model_map[complexity]
        logger.info(f"Selected model: {selected.value} for complexity: {complexity.value}")
        return selected

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    async def generate(
        self,
        prompt: str,
        model_type: Optional[ModelType] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate completion with automatic retry

        Args:
            prompt: Input prompt
            model_type: Specific model to use (auto-select if None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: System prompt for context

        Returns:
            Model response dictionary
        """
        if model_type is None:
            # Auto-assess complexity
            complexity = self.assess_complexity(
                text=prompt,
                signal_count=100,  # Default
                filing_type="10-K"  # Default
            )
            model_type = self.select_model(complexity)

        client = self.clients.get(model_type)
        if not client:
            raise ValueError(f"Model {model_type.value} not available")

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Make API call
            response = client.messages.create(
                model=model_type.value,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are an expert SEC filing analyst.",
                messages=messages
            )

            result = {
                "model": model_type.value,
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "stop_reason": response.stop_reason
            }

            logger.info(f"Generated completion with {model_type.value} ({result['usage']['output_tokens']} tokens)")
            return result

        except anthropic.APIError as e:
            logger.error(f"API error with {model_type.value}: {e}")
            raise

    async def analyze_signals(
        self,
        filing_data: Dict[str, Any],
        signals: Dict[str, List[Any]],
        complexity: Optional[ComplexityLevel] = None
    ) -> Dict[str, Any]:
        """
        Analyze extracted signals using appropriate model

        Args:
            filing_data: Parsed filing data
            signals: Extracted signals by category
            complexity: Override complexity assessment

        Returns:
            Analysis results
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(filing_data, signals)

        # Select model
        if complexity is None:
            complexity = self.assess_complexity(
                text=filing_data.get("text_content", ""),
                signal_count=sum(len(s) for s in signals.values()),
                filing_type=filing_data.get("form_type", "10-K"),
                custom_factors={
                    "table_count": len(filing_data.get("tables", [])),
                    "section_count": len(filing_data.get("sections", {}))
                }
            )

        model_type = self.select_model(complexity)

        # Generate analysis
        response = await self.generate(
            prompt=prompt,
            model_type=model_type,
            max_tokens=8192,
            system_prompt="""You are an expert financial analyst specializing in SEC filing analysis.
            Analyze the provided signals and provide actionable insights."""
        )

        return {
            "analysis": response["content"],
            "model_used": response["model"],
            "complexity": complexity.value,
            "usage": response["usage"]
        }

    def _build_analysis_prompt(
        self,
        filing_data: Dict[str, Any],
        signals: Dict[str, List[Any]]
    ) -> str:
        """Build prompt for signal analysis"""
        signal_summary = []
        for category, category_signals in signals.items():
            signal_summary.append(f"{category.value.upper()}: {len(category_signals)} signals")

        prompt = f"""Analyze the following SEC filing signals:

Filing Type: {filing_data.get('form_type', 'Unknown')}
Filing Date: {filing_data.get('filing_date', 'Unknown')}
Company CIK: {filing_data.get('cik', 'Unknown')}

Signal Summary:
{chr(10).join(signal_summary)}

Key Sections Available:
{', '.join(filing_data.get('sections', {}).keys())}

Tables: {len(filing_data.get('tables', []))} financial tables

Based on these signals, provide:
1. Overall financial health assessment
2. Key risk factors identified
3. Management sentiment analysis
4. Investment implications
5. Red flags or concerns

Be concise but thorough."""

        return prompt


class ModelLoadBalancer:
    """
    Load balancer for distributing requests across multiple API keys
    Useful for high-volume processing
    """

    def __init__(self, api_keys: List[str], model_type: ModelType):
        self.api_keys = api_keys
        self.model_type = model_type
        self.current_index = 0
        self.clients = [
            anthropic.Anthropic(api_key=key)
            for key in api_keys
        ]
        logger.info(f"Initialized load balancer with {len(self.clients)} clients")

    def get_next_client(self) -> anthropic.Anthropic:
        """Get next client in round-robin fashion"""
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.clients)
        return client

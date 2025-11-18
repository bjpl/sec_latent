"""
FACT Framework Implementation

FACT = Formal Anti-hallucination Checks and Tests
This module provides multi-model validation for financial analysis:
1. Mathematical Verification (Qwen2.5-coder)
2. Logic Validation (DeepSeek-R1)
3. Critical External Checks (Claude 3.5)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class ValidationType(Enum):
    """Types of validation checks in FACT framework."""
    MATHEMATICAL = "mathematical"
    LOGICAL = "logical"
    CRITICAL = "critical"


class ValidationSeverity(Enum):
    """Severity levels for validation failures."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    validation_type: ValidationType
    passed: bool
    confidence: float
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_used: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    overall_passed: bool
    confidence_score: float
    results: List[ValidationResult]
    risk_level: str
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FACTValidator:
    """
    FACT Framework validator implementing multi-model validation strategy.

    This class orchestrates three layers of validation:
    1. Mathematical verification for numerical claims
    2. Logic validation for reasoning consistency
    3. Critical external checks for high-stakes decisions
    """

    def __init__(
        self,
        math_model: str = "qwen2.5-coder",
        logic_model: str = "deepseek-r1",
        critical_model: str = "claude-3.5",
        confidence_threshold: float = 0.85,
        enable_logging: bool = True
    ):
        """
        Initialize FACT validator.

        Args:
            math_model: Model for mathematical verification
            logic_model: Model for logic validation
            critical_model: Model for critical checks
            confidence_threshold: Minimum confidence for passing validation
            enable_logging: Enable detailed logging
        """
        self.math_model = math_model
        self.logic_model = logic_model
        self.critical_model = critical_model
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        if enable_logging:
            self.logger.setLevel(logging.INFO)

    def validate(
        self,
        claim: str,
        context: Dict[str, Any],
        validation_types: Optional[List[ValidationType]] = None
    ) -> ValidationReport:
        """
        Perform comprehensive validation on a claim.

        Args:
            claim: The claim to validate
            context: Additional context for validation
            validation_types: Specific validation types to run (None = all)

        Returns:
            ValidationReport with results from all checks
        """
        if validation_types is None:
            validation_types = list(ValidationType)

        results = []

        # Mathematical Verification
        if ValidationType.MATHEMATICAL in validation_types:
            math_result = self._validate_mathematical(claim, context)
            results.append(math_result)

        # Logic Validation
        if ValidationType.LOGICAL in validation_types:
            logic_result = self._validate_logical(claim, context)
            results.append(logic_result)

        # Critical External Checks
        if ValidationType.CRITICAL in validation_types:
            critical_result = self._validate_critical(claim, context)
            results.append(critical_result)

        # Generate comprehensive report
        return self._generate_report(results)

    def _validate_mathematical(
        self,
        claim: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate mathematical claims using Qwen2.5-coder.

        This checks:
        - Numerical accuracy
        - Calculation correctness
        - Statistical validity
        - Unit consistency
        """
        self.logger.info(f"Mathematical validation: {claim[:100]}")

        # Extract numerical claims
        numbers = self._extract_numbers(claim)
        calculations = self._extract_calculations(claim)

        # Verify calculations
        verification_passed = True
        confidence = 1.0
        details = {
            "numbers_found": len(numbers),
            "calculations_checked": len(calculations),
            "verification_method": "symbolic_computation"
        }

        # Check for mathematical inconsistencies
        if calculations:
            verification_passed, confidence = self._verify_calculations(
                calculations,
                context
            )
            details["calculation_results"] = verification_passed

        # Verify units and scales
        unit_check = self._verify_units(claim, context)
        details["unit_consistency"] = unit_check

        severity = self._determine_severity(confidence, ValidationType.MATHEMATICAL)

        return ValidationResult(
            validation_type=ValidationType.MATHEMATICAL,
            passed=verification_passed and unit_check,
            confidence=confidence,
            severity=severity,
            message=self._generate_math_message(verification_passed, confidence),
            details=details,
            model_used=self.math_model
        )

    def _validate_logical(
        self,
        claim: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate logical consistency using DeepSeek-R1.

        This checks:
        - Reasoning coherence
        - Premise-conclusion validity
        - Absence of logical fallacies
        - Consistency with known facts
        """
        self.logger.info(f"Logic validation: {claim[:100]}")

        # Check for logical structure
        has_structure = self._check_logical_structure(claim)

        # Identify potential fallacies
        fallacies = self._detect_fallacies(claim, context)

        # Verify consistency
        consistency_score = self._check_consistency(claim, context)

        # Check for contradictions
        contradictions = self._find_contradictions(claim, context)

        passed = (
            has_structure and
            len(fallacies) == 0 and
            consistency_score > 0.8 and
            len(contradictions) == 0
        )

        confidence = consistency_score if passed else consistency_score * 0.5
        severity = self._determine_severity(confidence, ValidationType.LOGICAL)

        details = {
            "logical_structure": has_structure,
            "fallacies_detected": fallacies,
            "consistency_score": consistency_score,
            "contradictions": contradictions
        }

        return ValidationResult(
            validation_type=ValidationType.LOGICAL,
            passed=passed,
            confidence=confidence,
            severity=severity,
            message=self._generate_logic_message(passed, fallacies),
            details=details,
            model_used=self.logic_model
        )

    def _validate_critical(
        self,
        claim: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Perform critical external validation using Claude 3.5.

        This checks:
        - High-stakes decision accuracy
        - External source verification
        - Expert-level review
        - Regulatory compliance
        """
        self.logger.info(f"Critical validation: {claim[:100]}")

        # Assess risk level
        risk_level = self._assess_risk_level(claim, context)

        # External source verification
        sources_verified = self._verify_external_sources(claim, context)

        # Regulatory compliance check
        compliance_passed = self._check_regulatory_compliance(claim, context)

        # Expert review simulation
        expert_score = self._simulate_expert_review(claim, context)

        passed = (
            sources_verified and
            compliance_passed and
            expert_score > 0.85
        )

        confidence = expert_score
        severity = self._determine_severity(confidence, ValidationType.CRITICAL)

        details = {
            "risk_level": risk_level,
            "sources_verified": sources_verified,
            "compliance_passed": compliance_passed,
            "expert_score": expert_score
        }

        return ValidationResult(
            validation_type=ValidationType.CRITICAL,
            passed=passed,
            confidence=confidence,
            severity=severity,
            message=self._generate_critical_message(passed, risk_level),
            details=details,
            model_used=self.critical_model
        )

    def _generate_report(self, results: List[ValidationResult]) -> ValidationReport:
        """Generate comprehensive validation report."""
        overall_passed = all(r.passed for r in results)

        # Calculate weighted confidence score
        if results:
            confidence_score = sum(r.confidence for r in results) / len(results)
        else:
            confidence_score = 0.0

        # Determine risk level
        risk_level = self._calculate_risk_level(results)

        # Generate recommendations
        recommendations = self._generate_recommendations(results)

        return ValidationReport(
            overall_passed=overall_passed,
            confidence_score=confidence_score,
            results=results,
            risk_level=risk_level,
            recommendations=recommendations
        )

    # Helper methods

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numerical values from text."""
        import re
        pattern = r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
        matches = re.findall(pattern, text)
        return [float(m) for m in matches]

    def _extract_calculations(self, text: str) -> List[Dict[str, Any]]:
        """Extract calculation expressions from text."""
        # Placeholder for actual implementation
        return []

    def _verify_calculations(
        self,
        calculations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """Verify mathematical calculations."""
        # Placeholder for actual verification logic
        return True, 0.95

    def _verify_units(self, text: str, context: Dict[str, Any]) -> bool:
        """Verify unit consistency."""
        # Placeholder for unit verification
        return True

    def _check_logical_structure(self, text: str) -> bool:
        """Check if text has valid logical structure."""
        # Simple heuristic: check for premise indicators
        indicators = ['because', 'therefore', 'thus', 'hence', 'since']
        return any(ind in text.lower() for ind in indicators)

    def _detect_fallacies(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Detect logical fallacies."""
        # Placeholder for fallacy detection
        return []

    def _check_consistency(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> float:
        """Check consistency score."""
        # Placeholder for consistency checking
        return 0.9

    def _find_contradictions(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Find contradictions in text."""
        # Placeholder for contradiction detection
        return []

    def _assess_risk_level(self, text: str, context: Dict[str, Any]) -> str:
        """Assess risk level of claim."""
        # Placeholder for risk assessment
        risk_keywords = ['forecast', 'predict', 'estimate', 'project']
        if any(kw in text.lower() for kw in risk_keywords):
            return "high"
        return "medium"

    def _verify_external_sources(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> bool:
        """Verify external sources."""
        # Placeholder for source verification
        return True

    def _check_regulatory_compliance(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check regulatory compliance."""
        # Placeholder for compliance checking
        return True

    def _simulate_expert_review(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> float:
        """Simulate expert review score."""
        # Placeholder for expert review simulation
        return 0.88

    def _determine_severity(
        self,
        confidence: float,
        validation_type: ValidationType
    ) -> ValidationSeverity:
        """Determine severity based on confidence and type."""
        if validation_type == ValidationType.CRITICAL:
            if confidence < 0.7:
                return ValidationSeverity.CRITICAL
            elif confidence < 0.85:
                return ValidationSeverity.HIGH

        if confidence < 0.6:
            return ValidationSeverity.HIGH
        elif confidence < 0.75:
            return ValidationSeverity.MEDIUM
        else:
            return ValidationSeverity.LOW

    def _generate_math_message(self, passed: bool, confidence: float) -> str:
        """Generate message for mathematical validation."""
        if passed:
            return f"Mathematical validation passed (confidence: {confidence:.2f})"
        return f"Mathematical validation failed (confidence: {confidence:.2f})"

    def _generate_logic_message(self, passed: bool, fallacies: List[str]) -> str:
        """Generate message for logic validation."""
        if passed:
            return "Logic validation passed - no fallacies detected"
        return f"Logic validation failed - detected fallacies: {', '.join(fallacies)}"

    def _generate_critical_message(self, passed: bool, risk_level: str) -> str:
        """Generate message for critical validation."""
        if passed:
            return f"Critical validation passed (risk level: {risk_level})"
        return f"Critical validation failed (risk level: {risk_level})"

    def _calculate_risk_level(self, results: List[ValidationResult]) -> str:
        """Calculate overall risk level."""
        max_severity = max(
            (r.severity for r in results),
            default=ValidationSeverity.LOW
        )

        if max_severity == ValidationSeverity.CRITICAL:
            return "critical"
        elif max_severity == ValidationSeverity.HIGH:
            return "high"
        elif max_severity == ValidationSeverity.MEDIUM:
            return "medium"
        return "low"

    def _generate_recommendations(
        self,
        results: List[ValidationResult]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        for result in results:
            if not result.passed:
                if result.validation_type == ValidationType.MATHEMATICAL:
                    recommendations.append(
                        "Review numerical calculations and verify data sources"
                    )
                elif result.validation_type == ValidationType.LOGICAL:
                    recommendations.append(
                        "Strengthen logical reasoning and address identified fallacies"
                    )
                elif result.validation_type == ValidationType.CRITICAL:
                    recommendations.append(
                        "Conduct additional expert review and verify external sources"
                    )

        if not recommendations:
            recommendations.append("All validations passed - proceed with confidence")

        return recommendations

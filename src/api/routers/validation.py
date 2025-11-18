"""
Validation Router
Endpoints for FACT (Filing Analysis Consistency Testing) validation
"""

from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import logging

from ..cache import CacheKey

logger = logging.getLogger(__name__)

router = APIRouter()


class ValidationStatus(str, Enum):
    """Validation status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


class ValidationTest(BaseModel):
    """Individual validation test"""
    test_name: str
    description: str
    status: ValidationStatus
    details: str
    impact: str = Field(..., description="Impact level: low, medium, high, critical")
    recommendation: Optional[str] = None


class ValidationResult(BaseModel):
    """Complete validation result"""
    accession_number: str
    validation_id: str
    status: ValidationStatus
    timestamp: datetime
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_warning: int
    tests: List[ValidationTest]
    overall_score: float = Field(..., ge=0, le=100)
    summary: str


class ValidationRequest(BaseModel):
    """Validation request"""
    accession_number: str
    test_suite: str = Field(default="comprehensive", description="comprehensive, financial_only, compliance_only")
    strict_mode: bool = Field(default=False)


@router.post("/validate", response_model=ValidationResult)
async def validate_filing(
    request: Request,
    validation_req: ValidationRequest
):
    """
    Run FACT validation tests on filing

    Validates:
    - Financial statement consistency
    - Cross-reference accuracy
    - Regulatory compliance
    - Data quality
    - Format compliance
    """
    try:
        cache_params = validation_req.dict()
        if request.app.state.cache:
            cached = await request.app.state.cache.get(CacheKey.VALIDATION, cache_params)
            if cached:
                return cached

        # TODO: Implement actual validation tests
        tests = [
            ValidationTest(
                test_name="financial_consistency",
                description="Check balance sheet, income statement, and cash flow consistency",
                status=ValidationStatus.PASSED,
                details="All financial statements reconcile correctly",
                impact="high",
                recommendation=None
            ),
            ValidationTest(
                test_name="cross_reference_accuracy",
                description="Verify cross-references between sections",
                status=ValidationStatus.PASSED,
                details="All cross-references are accurate",
                impact="medium"
            ),
            ValidationTest(
                test_name="xbrl_validation",
                description="Validate XBRL data against schema",
                status=ValidationStatus.WARNING,
                details="Minor XBRL tag inconsistency detected",
                impact="low",
                recommendation="Review XBRL tags for non-standard usage"
            ),
            ValidationTest(
                test_name="disclosure_completeness",
                description="Check required disclosures are present",
                status=ValidationStatus.PASSED,
                details="All required disclosures present",
                impact="high"
            ),
            ValidationTest(
                test_name="format_compliance",
                description="Verify SEC format requirements",
                status=ValidationStatus.PASSED,
                details="Format complies with SEC regulations",
                impact="medium"
            )
        ]

        result = ValidationResult(
            accession_number=validation_req.accession_number,
            validation_id=f"VAL-{datetime.utcnow().timestamp()}",
            status=ValidationStatus.WARNING,  # Because one test has warning
            timestamp=datetime.utcnow(),
            tests_run=len(tests),
            tests_passed=sum(1 for t in tests if t.status == ValidationStatus.PASSED),
            tests_failed=sum(1 for t in tests if t.status == ValidationStatus.FAILED),
            tests_warning=sum(1 for t in tests if t.status == ValidationStatus.WARNING),
            tests=tests,
            overall_score=92.5,
            summary="Filing passed validation with minor warnings"
        )

        if request.app.state.cache:
            await request.app.state.cache.set(
                CacheKey.VALIDATION,
                result,
                cache_params,
                ttl=7200  # 2 hours
            )

        # Broadcast to WebSocket
        if request.app.state.ws_manager:
            await request.app.state.ws_manager.broadcast(
                {
                    "type": "validation_completed",
                    "validation_id": result.validation_id,
                    "accession_number": validation_req.accession_number,
                    "status": result.status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                channel="validation"
            )

        return result

    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Validation failed")


@router.get("/{validation_id}", response_model=ValidationResult)
async def get_validation_result(
    request: Request,
    validation_id: str
):
    """
    Get validation result by ID
    """
    try:
        cache_params = {"validation_id": validation_id}
        if request.app.state.cache:
            cached = await request.app.state.cache.get(CacheKey.VALIDATION, cache_params)
            if cached:
                return cached

        # TODO: Implement actual result retrieval
        raise HTTPException(status_code=404, detail="Validation not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Validation retrieval failed")


@router.get("/history/{accession_number}", response_model=List[ValidationResult])
async def get_validation_history(
    request: Request,
    accession_number: str,
    limit: int = Query(10, le=100)
):
    """
    Get validation history for a filing
    """
    try:
        cache_params = {"accession_number": accession_number, "limit": limit}
        if request.app.state.cache:
            cached = await request.app.state.cache.get(CacheKey.VALIDATION, cache_params)
            if cached:
                return cached

        # TODO: Implement actual history retrieval
        results = []

        if request.app.state.cache:
            await request.app.state.cache.set(
                CacheKey.VALIDATION,
                results,
                cache_params,
                ttl=3600
            )

        return results

    except Exception as e:
        logger.error(f"History retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="History retrieval failed")


@router.get("/tests/available")
async def get_available_tests():
    """
    Get list of available validation tests
    """
    return {
        "test_suites": [
            {
                "name": "comprehensive",
                "description": "All validation tests",
                "tests": 15
            },
            {
                "name": "financial_only",
                "description": "Financial statement validation only",
                "tests": 8
            },
            {
                "name": "compliance_only",
                "description": "Regulatory compliance checks only",
                "tests": 7
            }
        ],
        "individual_tests": [
            "financial_consistency",
            "cross_reference_accuracy",
            "xbrl_validation",
            "disclosure_completeness",
            "format_compliance",
            "date_consistency",
            "entity_information",
            "signature_verification",
            "exhibit_completeness",
            "narrative_quality",
            "risk_disclosure_adequacy",
            "management_discussion_analysis",
            "notes_to_financials",
            "segment_reporting",
            "related_party_transactions"
        ]
    }

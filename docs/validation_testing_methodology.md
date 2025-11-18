# Validation Testing Methodology

## Overview

This document describes the comprehensive testing methodology for the SEC filing analysis validation framework, including the FACT (Formal Anti-hallucination Checks and Tests) framework and GOALIE (Guarded Output Assessment and Liability-minimizing Intelligence Engine) protection system.

## Testing Philosophy

### Core Principles

1. **Test-First Development**: Write tests before or alongside implementation
2. **Comprehensive Coverage**: Aim for >80% code coverage across all components
3. **Realistic Scenarios**: Use real-world SEC filing examples
4. **Edge Case Focus**: Explicitly test boundary conditions and failure modes
5. **Performance Awareness**: Monitor and test performance characteristics
6. **Continuous Validation**: Run tests automatically on every change

## Test Pyramid

```
         /\
        /  \     E2E Tests (10%)
       /____\    - Complete workflows
      /      \   - Real data scenarios
     /________\
    /          \ Integration Tests (30%)
   /____________\  - FACT + GOALIE
  /              \ - Multi-component
 /________________\
/                  \ Unit Tests (60%)
/____________________\ - Individual functions
                       - Component isolation
```

## Test Coverage Matrix

### FACT Framework Testing

| Component | Unit Tests | Integration Tests | Coverage Target |
|-----------|------------|-------------------|-----------------|
| Mathematical Validation | ✅ 45 tests | ✅ 8 tests | 90% |
| Logic Validation | ✅ 38 tests | ✅ 6 tests | 90% |
| Critical Checks | ✅ 32 tests | ✅ 7 tests | 90% |
| Report Generation | ✅ 15 tests | ✅ 5 tests | 85% |

### GOALIE Protection Testing

| Component | Unit Tests | Integration Tests | Coverage Target |
|-----------|------------|-------------------|-----------------|
| Risk Assessment | ✅ 42 tests | ✅ 9 tests | 90% |
| Confidence Scoring | ✅ 35 tests | ✅ 7 tests | 90% |
| Prediction Adjustment | ✅ 28 tests | ✅ 6 tests | 85% |
| Display Rules | ✅ 18 tests | ✅ 4 tests | 85% |

### Validation Metrics Testing

| Component | Unit Tests | Integration Tests | Coverage Target |
|-----------|------------|-------------------|-----------------|
| Metrics Calculation | ✅ 25 tests | ✅ 5 tests | 90% |
| Threshold Validation | ✅ 15 tests | ✅ 3 tests | 85% |
| Metrics Tracking | ✅ 20 tests | ✅ 4 tests | 85% |
| Trend Analysis | ✅ 12 tests | ✅ 3 tests | 80% |

## Test Types and Strategies

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Strategy**:
- Mock external dependencies
- Test single responsibility
- Focus on pure functions
- Verify edge cases

**Example**:
```python
def test_extract_numbers(self):
    """Test extraction of numerical values from text."""
    text = "Revenue: $123.45M, Profit: 67.8%"
    numbers = self.validator._extract_numbers(text)

    self.assertIn(123.45, numbers)
    self.assertIn(67.8, numbers)
```

### 2. Integration Tests

**Purpose**: Test component interactions

**Strategy**:
- Test real component integration
- Minimal mocking
- Focus on data flow
- Verify end-to-end behavior

**Example**:
```python
def test_complete_validation_pipeline(self):
    """Test FACT validation followed by GOALIE protection."""
    claim = "Revenue forecast: $150M"

    fact_report = self.fact.validate(claim, context)
    goalie_result = self.goalie.protect(
        prediction,
        context,
        model_outputs
    )

    self.assertLess(goalie_result.adjustment_factor, 1.0)
```

### 3. Edge Case Tests

**Purpose**: Test boundary conditions and unusual inputs

**Scenarios Tested**:
- Empty inputs
- Extremely large values
- Malformed data
- Unicode and special characters
- Contradictory statements
- Missing context

**Example**:
```python
def test_special_characters(self):
    """Test validation with special characters."""
    claim = "Revenue: $100M (Q1) → $125M (Q2) ≈ 25% ↑"
    report = self.validator.validate(claim, {})
    self.assertIsNotNone(report)
```

### 4. Performance Tests

**Purpose**: Verify performance characteristics

**Metrics Tracked**:
- Single validation latency
- Batch processing throughput
- Memory usage
- Concurrent request handling

**Example**:
```python
def test_batch_validation_performance(self):
    """Test performance with batch validations."""
    claims = [f"Revenue: ${100+i}M" for i in range(100)]

    start = time.time()
    for claim in claims:
        self.validator.validate(claim, {})
    duration = time.time() - start

    self.assertLess(duration, 10.0)  # < 100ms per validation
```

## Test Data and Fixtures

### Test Data Sources

1. **Synthetic Data**: Generated test cases covering common patterns
2. **Real SEC Filings**: Anonymized excerpts from actual filings
3. **Edge Cases**: Manually crafted boundary conditions
4. **Historical Errors**: Past validation failures

### Fixture Organization

```python
# fixtures.py structure
ValidationTestFixtures
├── get_financial_claims()      # Financial statement tests
├── get_logical_claims()         # Reasoning tests
├── get_mathematical_claims()    # Calculation tests
├── get_model_outputs()          # Mock model responses
├── get_risk_contexts()          # Risk scenario contexts
└── get_edge_cases()             # Boundary conditions
```

## Validation Quality Metrics

### Code Coverage Targets

- **Overall**: ≥ 80%
- **Critical Paths**: ≥ 90%
- **Risk Assessment**: ≥ 90%
- **UI/Adapters**: ≥ 70%

### Quality Gates

✅ All tests must pass
✅ Coverage ≥ 80%
✅ No critical security issues
✅ Performance benchmarks met
✅ Documentation updated

## Continuous Testing

### Automated Testing Pipeline

1. **Pre-commit Hooks**
   - Run fast unit tests
   - Check code formatting
   - Verify imports

2. **Pull Request Checks**
   - Full test suite
   - Coverage analysis
   - Performance benchmarks
   - Security scanning

3. **Nightly Builds**
   - Extended test suite
   - Integration tests
   - Performance regression tests
   - Documentation validation

### Test Execution Schedule

| Trigger | Tests Run | Frequency |
|---------|-----------|-----------|
| File save | Fast unit tests | On change |
| Git commit | Core unit tests | Per commit |
| PR creation | Full unit + integration | Per PR |
| Merge to main | Complete suite | Per merge |
| Nightly | Extended + performance | Daily |

## Testing Best Practices

### 1. Test Structure

**AAA Pattern** (Arrange-Act-Assert):
```python
def test_risk_assessment(self):
    # Arrange
    prediction = "Revenue forecast"
    context = {"forecast": True}

    # Act
    assessment = self.goalie.assess_risk(prediction, context)

    # Assert
    self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
```

### 2. Test Naming

**Convention**: `test_<component>_<scenario>_<expected_behavior>`

Good examples:
- `test_mathematical_validation_pass`
- `test_confidence_scoring_high_agreement`
- `test_risk_assessment_critical_high_confidence`

### 3. Test Independence

Each test should:
- Set up its own fixtures
- Clean up after itself
- Not depend on other tests
- Be runnable in any order

### 4. Assertion Quality

**Good**:
```python
self.assertEqual(result.risk_level, RiskLevel.HIGH)
self.assertIn("disclaimer", result.explanation)
```

**Bad**:
```python
self.assertTrue(result)  # Too vague
self.assertEqual(len(result), 5)  # Magic numbers
```

## Failure Mode Testing

### Categories of Failures Tested

1. **Input Validation Failures**
   - Empty inputs
   - Malformed data
   - Type mismatches

2. **Business Logic Failures**
   - Invalid calculations
   - Logical contradictions
   - Threshold violations

3. **System Failures**
   - Model timeouts
   - Resource exhaustion
   - Concurrent access issues

4. **Data Quality Failures**
   - Missing required fields
   - Inconsistent data
   - Corrupted inputs

### Example Failure Test

```python
def test_cascading_failures(self):
    """Test behavior when multiple validations fail."""
    claim = "Invalid illogical forecast with wrong math"
    context = {
        "uncertainty_high": True,
        "data_quality": 0.2
    }

    fact_report = self.fact.validate(claim, context)
    goalie_result = self.goalie.protect(claim, context)

    # Should apply maximum protection
    self.assertLess(goalie_result.adjustment_factor, 0.7)
```

## Metrics and Reporting

### Test Metrics Tracked

- **Execution Time**: Per test and total
- **Coverage**: Line, branch, and function coverage
- **Flakiness**: Tests that fail intermittently
- **Performance**: Latency and throughput

### Reports Generated

1. **Coverage Report** (HTML)
   - Line-by-line coverage
   - Branch coverage
   - Missing coverage highlights

2. **Performance Report** (JSON)
   - Execution times
   - Performance trends
   - Benchmark comparisons

3. **Quality Report** (Markdown)
   - Test pass rates
   - Coverage metrics
   - Quality gate status

## Debugging Failed Tests

### Debug Workflow

1. **Read Error Message**: Understand what failed
2. **Check Test Name**: Understand what's being tested
3. **Review Assertions**: See what was expected vs. actual
4. **Run in Isolation**: `pytest test_file.py::TestClass::test_method -v`
5. **Add Debug Prints**: Use `-s` flag to see print statements
6. **Use Debugger**: `pytest --pdb` to drop into debugger

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | PYTHONPATH not set | Run from project root |
| Timeout | Test too slow | Increase timeout or optimize |
| Flaky test | Race condition | Add proper synchronization |
| Assertion failure | Logic error | Review test logic |

## Future Enhancements

### Planned Improvements

1. **Property-Based Testing**
   - Use Hypothesis for generative testing
   - Discover edge cases automatically

2. **Mutation Testing**
   - Verify test quality
   - Ensure tests actually catch bugs

3. **Performance Regression Testing**
   - Automatic performance tracking
   - Alert on significant degradation

4. **Chaos Engineering**
   - Inject random failures
   - Test system resilience

## References

- Test Implementation: `tests/validation/`
- Configuration: `config/validation_config.yaml`
- FACT Documentation: `docs/fact_framework.md`
- GOALIE Documentation: `docs/goalie_protection.md`

# Validation Framework Test Suite

Comprehensive test suite for the FACT framework and GOALIE protection system.

## Test Structure

```
tests/validation/
├── __init__.py                 # Test package initialization
├── test_fact.py               # FACT framework unit tests
├── test_goalie.py             # GOALIE protection unit tests
├── test_metrics.py            # Validation metrics tests
├── test_integration.py        # Integration tests
├── fixtures.py                # Test fixtures and mock data
└── README.md                  # This file
```

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/validation/ -v

# With coverage
python -m pytest tests/validation/ --cov=src/validation --cov-report=html
```

### Run Specific Test Files
```bash
# FACT tests only
python -m pytest tests/validation/test_fact.py -v

# GOALIE tests only
python -m pytest tests/validation/test_goalie.py -v

# Integration tests only
python -m pytest tests/validation/test_integration.py -v
```

### Run Specific Test Cases
```bash
# Run a specific test class
python -m pytest tests/validation/test_fact.py::TestFACTValidator -v

# Run a specific test method
python -m pytest tests/validation/test_fact.py::TestFACTValidator::test_mathematical_validation_pass -v
```

## Test Categories

### 1. Unit Tests (`test_fact.py`, `test_goalie.py`, `test_metrics.py`)

**Purpose**: Test individual components in isolation

**Coverage**:
- FACT framework mathematical validation
- FACT framework logical validation
- FACT framework critical checks
- GOALIE risk assessment
- GOALIE confidence scoring
- GOALIE prediction adjustment
- Validation metrics calculation
- Metrics tracking and trending

**Key Test Classes**:
- `TestFACTValidator`: Core FACT functionality
- `TestValidationEdgeCases`: Edge cases for FACT
- `TestGOALIEProtection`: Core GOALIE functionality
- `TestGOALIEEdgeCases`: Edge cases for GOALIE
- `TestMetricsCalculator`: Metrics calculation
- `TestMetricsTracker`: Metrics tracking over time

### 2. Integration Tests (`test_integration.py`)

**Purpose**: Test complete validation pipeline

**Coverage**:
- FACT + GOALIE integration
- Multi-model consensus validation
- End-to-end validation workflows
- Failure mode handling
- Performance testing

**Key Test Classes**:
- `TestFACTGOALIEIntegration`: Complete pipeline tests
- `TestFailureModes`: Error handling and recovery
- `TestPerformance`: Performance and scalability

### 3. Test Fixtures (`fixtures.py`)

**Purpose**: Provide reusable test data and mocks

**Available Fixtures**:
- `ValidationTestFixtures`: Common test data
- `MockModelInterface`: Mock model for testing
- `ValidationScenarios`: Pre-defined test scenarios

## Test Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| FACT Framework | 90% | ✅ Implemented |
| GOALIE Protection | 90% | ✅ Implemented |
| Validation Metrics | 85% | ✅ Implemented |
| Integration | 80% | ✅ Implemented |

## Adding New Tests

### 1. Unit Tests

Add tests to appropriate test file:

```python
# In test_fact.py
def test_new_validation_feature(self):
    """Test description."""
    validator = FACTValidator()
    result = validator.new_feature(test_input)
    self.assertEqual(result, expected_output)
```

### 2. Integration Tests

Add to `test_integration.py`:

```python
def test_new_workflow(self):
    """Test new validation workflow."""
    fact = FACTValidator()
    goalie = GOALIEProtection()

    # Test complete workflow
    fact_result = fact.validate(claim, context)
    goalie_result = goalie.protect(prediction, context)

    self.assertIsNotNone(goalie_result)
```

### 3. Test Fixtures

Add to `fixtures.py`:

```python
@staticmethod
def get_new_test_data() -> List[Dict[str, Any]]:
    """Get new test data."""
    return [
        {
            "input": "test_value",
            "expected": "expected_result"
        }
    ]
```

## Test Configuration

Configuration file: `config/validation_config.yaml`

Key settings:
- Model assignments
- Confidence thresholds
- Risk categories
- Adjustment factors
- Testing parameters

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Nightly builds

CI Requirements:
- All tests must pass
- Coverage must be ≥ 80%
- No test duration > 60 seconds

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
**Solution**: Ensure you're running from project root and src is in PYTHONPATH

**Issue**: Tests timeout
**Solution**: Check `timeout_seconds` in config or use `-v` flag for verbose output

**Issue**: Coverage report missing
**Solution**: Install pytest-cov: `pip install pytest-cov`

### Debug Mode

Run tests with additional debugging:

```bash
# Maximum verbosity
python -m pytest tests/validation/ -vvv

# Show print statements
python -m pytest tests/validation/ -s

# Stop on first failure
python -m pytest tests/validation/ -x

# Drop into debugger on failure
python -m pytest tests/validation/ --pdb
```

## Performance Benchmarks

Target performance metrics:

| Operation | Target Time | Acceptable Range |
|-----------|-------------|------------------|
| Single FACT validation | < 100ms | 50-200ms |
| Single GOALIE protection | < 50ms | 20-100ms |
| Complete pipeline | < 150ms | 100-300ms |
| Batch (100 items) | < 10s | 5-20s |

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test method names
3. **Single Assertion Focus**: Test one behavior per test
4. **Use Fixtures**: Reuse test data from fixtures
5. **Document Edge Cases**: Clearly document unusual test scenarios
6. **Mock External Dependencies**: Don't rely on external services
7. **Test Both Paths**: Test success and failure cases
8. **Performance Awareness**: Keep tests fast

## Contributing

When contributing tests:

1. Follow existing test structure
2. Add docstrings to test methods
3. Update this README if adding new test categories
4. Ensure all tests pass locally before submitting
5. Aim for >80% coverage on new code
6. Add integration tests for new features

## Contact

For questions about testing:
- Check existing test examples
- Review fixtures for available test data
- Consult validation framework documentation

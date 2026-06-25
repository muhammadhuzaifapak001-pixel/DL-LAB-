# Unit Tests for Plant Disease Detection

Comprehensive pytest test suite for model validation, data loading, and API functionality.

## Running Tests

### Install dependencies
```bash
pip install pytest pytest-cov
```

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ -v --cov=src --cov=deployment --cov-report=html --cov-report=term
```

### Run specific test class
```bash
pytest tests/test_models.py::TestModels -v
```

### Run specific test function
```bash
pytest tests/test_models.py::TestModels::test_baseline_output_shape -v
```

## Test Coverage

### Model Tests (TestModels)
- ✅ Model instantiation (BaselineCNN, ImprovedCNN)
- ✅ Output shape validation (correct batch and class dimensions)
- ✅ Forward pass validation (no NaN values)
- ✅ get_model factory function
- ✅ Different number of classes support
- ✅ Model parameter trainability
- ✅ Architecture comparison (v2 > v1 parameters)

### Data Tests (TestTransforms)
- ✅ Transform availability (train/eval)
- ✅ Train transforms include augmentation
- ✅ Eval transforms don't have augmentation

### Evaluation Tests (TestEvaluation)
- ✅ evaluate_model function works
- ✅ Returns scalar float values
- ✅ Loss >= 0 and 0 <= accuracy <= 100

### Deployment Tests (TestDeploymentUtils)
- ✅ Utility function imports
- ✅ Class names JSON loading
- ✅ Missing file error handling

### API Tests (TestAPIEndpoints)
- ✅ FastAPI app can be imported
- ✅ get_model function accessibility

### Data Validation Tests (TestDataValidation)
- ✅ Variable batch size handling
- ✅ Graceful failure with wrong dimensions

### Serialization Tests (TestModelSerialization)
- ✅ Model state save/load
- ✅ Parameter preservation

## Expected Results

All tests should pass:
```
tests/test_models.py::TestModels::test_baseline_instantiation PASSED
tests/test_models.py::TestModels::test_baseline_output_shape PASSED
tests/test_models.py::TestModels::test_baseline_forward_pass PASSED
tests/test_models.py::TestModels::test_improved_instantiation PASSED
tests/test_models.py::TestModels::test_improved_output_shape PASSED
tests/test_models.py::TestModels::test_improved_forward_pass PASSED
...
============= 25 passed in 2.34s =============
```

## CI/CD Integration

These tests are automatically run by GitHub Actions on every push/PR:
- Linting (flake8, black, pylint)
- Type checking (mypy)
- Unit tests (pytest)

See `.github/workflows/ci-cd.yml` for configuration.

## Adding New Tests

1. Add test class/function in `test_models.py`
2. Use descriptive names: `test_<feature>_<expected_behavior>`
3. Include docstrings explaining what is tested
4. Mark with pytest decorators if needed: `@pytest.mark.skip`, `@pytest.mark.xfail`

Example:
```python
def test_new_feature():
    """Test description here."""
    # Arrange
    model = BaselineCNN(num_classes=15)
    
    # Act
    result = model(torch.randn(2, 3, 224, 224))
    
    # Assert
    assert result.shape == (2, 15)
```

## Troubleshooting

**ImportError: No module named 'src'**
- Run pytest from project root: `cd /path/to/DL(Lab)` then `pytest tests/`

**CUDA errors in tests**
- Tests use CPU by default. Disable CUDA if issues persist:
  ```bash
  CUDA_VISIBLE_DEVICES="" pytest tests/
  ```

**Permission errors on Windows**
- Use WSL or PowerShell with proper path escaping

## Coverage Goals

- **Target**: >80% code coverage
- **Current**: Tests cover model, data, deployment modules
- **Future**: Add integration tests for end-to-end workflows

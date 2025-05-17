# Tests for Jenkins Pipeline Generator

This directory contains tests for the Jenkins Pipeline Generator API and model.

## Test Files

- `test_api.py` - Tests for the API endpoints
- `test_model_handler.py` - Tests for the JenkinsPipelineGenerator class
- `test_integration.py` - Integration tests for the complete flow

## Running Tests

Install the test dependencies:

```bash
pip install -r requirements-test.txt
```

Run all tests:

```bash
pytest
```

Run specific tests:

```bash
# Run API tests
pytest tests/test_api.py

# Run model handler tests
pytest tests/test_model_handler.py

# Run integration tests
pytest tests/test_integration.py
```

Run tests with verbose output:

```bash
pytest -v
```

## Test Coverage

To run tests with coverage:

```bash
pytest --cov=src tests/
```

## Continuous Integration

These tests are designed to be run in a CI environment. Add the following to your CI configuration:

```yaml
test:
  script:
    - pip install -r tests/requirements-test.txt
    - pytest tests/
``` 
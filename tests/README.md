# 🧪 Cacherr Backend Testing Suite

A comprehensive testing framework for the Cacherr backend, following Python-pro standards with extensive test coverage, performance benchmarks, and detailed documentation.

## 📋 Overview

This testing suite provides multiple layers of testing:

- **Unit Tests**: Isolated component testing with comprehensive mocking
- **Integration Tests**: Multi-component interaction testing
- **API Tests**: HTTP endpoint testing with realistic request/response validation
- **WebSocket Tests**: Real-time communication testing
- **Security Tests**: Authentication, authorization, and vulnerability testing
- **Performance Tests**: Benchmarks and load testing
- **Repository Tests**: Database and data access layer testing

## 🚀 Quick Start

### Install Test Dependencies
```bash
# From the project root
pip install -r tests/requirements.txt
```

### Run All Tests
```bash
# Using the test runner script
python tests/run_tests.py --all

# Or directly with pytest
pytest
```

### Run Specific Test Types
```bash
# Unit tests only (fastest)
python tests/run_tests.py --unit

# Integration tests
python tests/run_tests.py --integration

# API tests
python tests/run_tests.py --api

# With coverage reporting
python tests/run_tests.py --coverage

# Fast tests only (parallel execution)
python tests/run_tests.py --fast --parallel
```

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini              # Pytest configuration
├── setup.cfg              # Tool configurations (mypy, black, etc.)
├── requirements.txt       # Test dependencies
├── run_tests.py           # Test runner script
├── README.md              # This file
├── fixtures/              # Test data and fixtures
│   └── data/             # Static test data
├── mocks/                 # Mock implementations
│   └── service_mocks.py   # Reusable service mocks
├── unit/                  # Unit tests (fast, isolated)
│   ├── core/             # Core component tests
│   ├── repositories/     # Repository layer tests
│   └── utils/            # Utility function tests
├── integration/           # Integration tests (multi-component)
│   └── test_application_integration.py
└── utils/                 # Test utilities and helpers
    └── test_helpers.py   # Shared test helper functions
```

## 🏷️ Test Markers

Tests are categorized using pytest markers for selective execution:

| Marker | Description | Example Usage |
|--------|-------------|---------------|
| `@pytest.mark.unit` | Fast unit tests (< 0.1s) | `pytest -m unit` |
| `@pytest.mark.integration` | Multi-component tests (< 1s) | `pytest -m integration` |
| `@pytest.mark.api` | HTTP endpoint tests | `pytest -m api` |
| `@pytest.mark.websocket` | WebSocket functionality | `pytest -m websocket` |
| `@pytest.mark.repository` | Database/repository layer | `pytest -m repository` |
| `@pytest.mark.service` | Business logic services | `pytest -m service` |
| `@pytest.mark.security` | Security and auth tests | `pytest -m security` |
| `@pytest.mark.performance` | Performance benchmarks | `pytest -m performance` |
| `@pytest.mark.slow` | Slow tests (> 1s) | `pytest -m slow` |
| `@pytest.mark.external` | Tests requiring external services | `pytest -m "not external"` |

## 🔧 Test Runner Features

The `run_tests.py` script provides advanced testing capabilities:

### Selective Test Execution
```bash
# Run only unit tests
python tests/run_tests.py --unit

# Run only service layer tests
python tests/run_tests.py --service

# Run security tests only
python tests/run_tests.py --security

# Run performance tests
python tests/run_tests.py --performance
```

### Parallel Execution
```bash
# Run tests in parallel (automatic worker detection)
python tests/run_tests.py --parallel

# Run fast tests in parallel
python tests/run_tests.py --fast --parallel
```

### Coverage Reporting
```bash
# Generate coverage reports
python tests/run_tests.py --coverage

# Coverage reports are saved to:
# - htmlcov/index.html (HTML report)
# - coverage.xml (XML for CI/CD)
# - Terminal output with missing lines
```

### Utility Commands
```bash
# Check test file structure
python tests/run_tests.py --check-structure

# Generate comprehensive test report
python tests/run_tests.py --generate-report

# Run only slow tests
python tests/run_tests.py --slow
```

## 📊 Coverage Requirements

The test suite enforces high coverage standards:

- **Overall Coverage**: ≥90%
- **Branch Coverage**: Enabled for conditional logic testing
- **Source Code**: All files in `src/` directory
- **Exclusions**: Test files, migrations, and generated code

### Coverage Report Analysis
```bash
# View coverage in terminal
pytest --cov=src --cov-report=term-missing

# Open HTML coverage report
open htmlcov/index.html

# Generate XML report for CI/CD
pytest --cov=src --cov-report=xml
```

## 🛠️ Fixtures and Test Data

### Shared Fixtures (conftest.py)

| Fixture | Purpose | Scope |
|---------|---------|-------|
| `test_config` | Test configuration settings | Session |
| `temp_dir` | Temporary directory for tests | Function |
| `test_data_dir` | Path to test data directory | Function |
| `mock_config` | Mock configuration for testing | Function |
| `clean_container` | Clean DI container | Function |
| `configured_container` | Container with test services | Function |
| `test_cache_repository` | Test cache repository | Function |
| `test_config_repository` | Test config repository | Function |
| `test_metrics_repository` | Test metrics repository | Function |
| `test_application` | Test application context | Function |
| `started_test_application` | Started test application | Function |
| Various service mocks | Mock implementations | Function |

### Test Data Management
- Static test data in `tests/fixtures/data/`
- Dynamic test data generation with Faker
- Factory Boy patterns for complex object creation
- Temporary file/directory management

## 🔒 Security Testing

Comprehensive security testing includes:

- **Input Validation**: SQL injection, XSS, path traversal prevention
- **Authentication**: Token validation, session management
- **Authorization**: Permission checking, role-based access
- **Data Protection**: Encryption, secure storage
- **Rate Limiting**: DoS protection mechanisms
- **Audit Logging**: Security event tracking

### Security Test Examples
```python
@pytest.mark.security
def test_sql_injection_prevention(temp_db_service):
    """Test that SQL injection attempts are blocked."""
    # Implementation tests query sanitization

@pytest.mark.security
def test_path_traversal_protection(temp_db_service):
    """Test that path traversal attacks are prevented."""
    # Implementation tests path validation
```

## ⚡ Performance Testing

Performance tests ensure the application meets performance requirements:

- **Response Times**: API endpoint performance benchmarks
- **Memory Usage**: Memory consumption monitoring
- **Concurrent Operations**: Multi-user load testing
- **Database Performance**: Query optimization validation
- **Resource Usage**: CPU and I/O monitoring

### Performance Test Examples
```python
@pytest.mark.performance
def test_api_response_times(benchmark):
    """Benchmark API response times."""
    # Implementation measures response latency

@pytest.mark.performance
def test_concurrent_operations():
    """Test performance under concurrent load."""
    # Implementation tests multi-threading performance
```

## 📈 Continuous Integration

### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    python tests/run_tests.py --all --coverage --parallel

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```bash
# Run tests before committing
pre-commit run --all-files

# Or install pre-commit hooks
pre-commit install
```

## 🐛 Debugging Tests

### Test Debugging Techniques
```bash
# Run specific test with debugging
pytest tests/unit/test_specific.py::TestClass::test_method -v -s

# Drop into debugger on failure
pytest --pdb

# Show captured output
pytest -v -s

# Run tests with coverage details
pytest --cov=src --cov-report=term-missing:skip-covered
```

### Common Issues and Solutions

**Slow Tests**
- Use `@pytest.mark.unit` for fast tests
- Mock external dependencies
- Use temporary databases in memory

**Flaky Tests**
- Avoid time-dependent tests
- Use proper fixtures for setup/teardown
- Mock external services consistently

**Coverage Gaps**
- Add tests for error conditions
- Test edge cases and boundary values
- Ensure all code paths are exercised

## 📝 Writing New Tests

### Test File Naming Convention
- Unit tests: `test_component.py`
- Integration tests: `test_feature_integration.py`
- API tests: `test_api_endpoints.py`

### Test Class Structure
```python
import pytest
from unittest.mock import Mock

class TestComponentName:
    """Test suite for ComponentName."""

    def test_successful_operation(self, fixture_name):
        """Test successful operation with valid inputs."""
        # Arrange
        component = ComponentName()
        valid_input = "valid_data"

        # Act
        result = component.process(valid_input)

        # Assert
        assert result.success is True
        assert result.data == "expected_output"

    def test_error_handling(self, fixture_name):
        """Test error handling with invalid inputs."""
        # Arrange
        component = ComponentName()
        invalid_input = None

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid input"):
            component.process(invalid_input)
```

### Fixture Usage
```python
@pytest.fixture
def component_with_dependencies(mock_service):
    """Create component with mocked dependencies."""
    return ComponentName(service=mock_service)

def test_component_functionality(component_with_dependencies):
    """Test component using fixture."""
    result = component_with_dependencies.process("input")
    assert result is not None
```

## 📋 Test Reports and Documentation

### Generated Reports
- **HTML Reports**: `htmlcov/index.html` (coverage)
- **XML Reports**: `coverage.xml` (CI/CD integration)
- **JSON Reports**: `reports/test_report.json` (programmatic access)
- **JUnit XML**: `reports/test_report.xml` (test results)

### Documentation Standards
- Comprehensive docstrings for all test methods
- Clear test naming that describes what is being tested
- Comments explaining complex test setups
- References to requirements or specifications

## 🎯 Best Practices

### Test Organization
1. **One Concept Per Test**: Each test should verify one specific behavior
2. **Descriptive Names**: Test names should clearly describe what is being tested
3. **Arrange-Act-Assert**: Follow the three-phase test structure
4. **Independent Tests**: Tests should not depend on each other

### Mocking Strategy
1. **Minimal Mocking**: Mock only external dependencies
2. **Consistent Mocks**: Use shared fixtures for common mocks
3. **Verification**: Verify mock interactions where relevant
4. **Real Objects**: Prefer real objects over mocks when possible

### Performance Considerations
1. **Fast Tests**: Keep unit tests under 100ms
2. **Parallel Execution**: Design tests to run in parallel
3. **Resource Cleanup**: Properly clean up resources in fixtures
4. **Selective Running**: Use markers to skip slow tests in development

This testing framework ensures the Cacherr backend maintains high quality, performance, and security standards through comprehensive automated testing.

# Testing Guide for Anomaly Detector

This document provides instructions for running and writing tests for the Anomaly Detector project.

## Test Structure

Tests are organized by service/module:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration
├── test_auth.py             # Authentication service tests
├── test_anomaly_service.py  # Anomaly detection service tests
├── test_ml_service.py       # Machine learning service tests
├── test_rbac.py             # RBAC and security tests
└── test_monitoring.py       # Monitoring and observability tests
```

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Environment Setup

Tests use an in-memory SQLite database by default, so no external dependencies are required.

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/test_auth.py
```

### Run Specific Test Class

```bash
pytest tests/test_auth.py::TestUserAuthentication
```

### Run Specific Test Function

```bash
pytest tests/test_auth.py::TestUserAuthentication::test_register_user_success
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run security tests
pytest -m security

# Skip slow tests
pytest -m "not slow"
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Detailed Output and Failed Test Info

```bash
pytest -vv -ra
```

## Test Categories

Tests are categorized with pytest markers for easy filtering:

- **unit**: Fast, isolated tests
- **integration**: Tests requiring external services
- **asyncio**: Asynchronous tests
- **slow**: Tests that take longer to run
- **security**: RBAC and permission tests
- **monitoring**: Performance and health check tests

## Writing New Tests

### Test File Naming

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<specific_behavior>`

### Example Test Structure

```python
import pytest
from src.services.my_service import MyService

@pytest.fixture
def my_service():
    """Provide MyService instance"""
    return MyService()

class TestMyFeature:
    """Test suite for MyFeature"""

    def test_feature_success(self, my_service):
        """Test successful feature behavior"""
        result = my_service.do_something()
        assert result is not None
        assert result.status == "success"

    def test_feature_failure(self, my_service):
        """Test failure case"""
        with pytest.raises(ValueError):
            my_service.do_something_invalid()
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

- `db_session`: Fresh database session for each test
- `test_client`: FastAPI test client
- `admin_user`: Admin test user
- `analyst_user`: Analyst test user
- `auditor_user`: Auditor test user
- `guest_user`: Guest test user

Example:

```python
def test_with_user(db_session, admin_user):
    """Test using fixtures"""
    assert admin_user.role == "admin"
    # Use db_session for database operations
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function(self):
    """Test async behavior"""
    result = await my_async_function()
    assert result is not None
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines. Key points:

- All tests must pass before merge
- Code coverage should be maintained above 80%
- No external service dependencies for unit tests
- Tests must be portable and runnable on any machine

## Debugging Tests

### Run with Print Statements Visible

```bash
pytest -s
```

### Run with Python Debugger

```bash
pytest --pdb
```

This will drop into the debugger on test failure.

### Run Single Test in Debug Mode

```bash
pytest -s --pdb tests/test_auth.py::TestUserAuthentication::test_login_success
```

## Test Data

### Using Factories

For complex test data, use the Faker library:

```python
from faker import Faker

def test_with_fake_data():
    fake = Faker()
    username = fake.user_name()
    email = fake.email()
```

### Using Freezegun for Time

```python
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00")
def test_with_frozen_time():
    now = datetime.utcnow()
    assert now.year == 2024
```

## Best Practices

1. **One assertion per test** (when possible)
   - Easier to debug and understand test failures

2. **Use descriptive test names**
   - Test name should describe what is being tested and expected outcome

3. **Keep tests independent**
   - Tests should not depend on order or state from other tests

4. **Use fixtures for setup**
   - Avoid duplicating setup code

5. **Mock external dependencies**
   - Tests should not make real HTTP calls or access external services

6. **Test edge cases**
   - Null values, empty lists, boundary conditions

7. **Keep tests fast**
   - Optimize database queries and avoid slow operations

## Troubleshooting

### Import Errors

If you get import errors, ensure the project root is in `PYTHONPATH`:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

Or use the standard Python invocation:

```bash
python -m pytest
```

### Database Lock Issues

If tests fail with database lock errors:

```bash
pytest -n auto  # Run tests in parallel
```

Or ensure `test_db_session` fixture properly closes connections.

### Async Test Issues

If async tests fail with `RuntimeError: no running event loop`:

Ensure `@pytest.mark.asyncio` decorator is present.

## Performance

Run tests with timing information:

```bash
pytest --durations=10
```

This shows the 10 slowest tests, helping identify optimization opportunities.

## Coverage Reports

Generate and view coverage report:

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

Aim for >80% coverage on critical paths.

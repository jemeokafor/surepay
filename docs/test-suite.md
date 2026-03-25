# SurePay Backend Test Suite

## Overview

This document describes the comprehensive test suite for the SurePay backend API. The test suite includes unit tests, integration tests, and end-to-end tests to ensure the reliability and correctness of the application.

## Test Structure

```
backend/tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_config.py       # Configuration tests
├── test_security.py     # Security module tests
├── test_health.py       # Health check endpoint tests
├── test_webhooks.py     # Paystack webhook endpoint tests
├── test_payments.py     # Payment endpoint tests
├── test_payouts.py       # Payout endpoint tests
├── test_supabase_service.py  # Supabase service unit tests
├── test_paystack_service.py  # Paystack service unit tests
└── test_integration.py  # Integration and end-to-end flow tests
```

## Test Categories

### 1. Unit Tests

Unit tests focus on individual functions and components:

- **Configuration Tests** (`test_config.py`): Test environment variable loading and configuration parsing
- **Security Tests** (`test_security.py`): Test signature verification and security functions
- **Service Tests** (`test_supabase_service.py`, `test_paystack_service.py`): Test individual service methods with mocked dependencies

### 2. API Endpoint Tests

API tests verify that endpoints return correct responses:

- **Health Check Tests** (`test_health.py`): Test `/health` endpoints
- **Webhook Tests** (`test_webhooks.py`): Test Paystack webhook handling
- **Payment Tests** (`test_payments.py`): Test payment initialization and verification
- **Payout Tests** (`test_payouts.py`): Test payout creation and retry functionality

### 3. Integration Tests

Integration tests verify complete workflows:

- **Payment Flow** (`test_integration.py`): Test complete payment flow from initialization to webhook confirmation
- **Payout Flow** (`test_integration.py`): Test complete payout flow from creation to webhook confirmation
- **Retry Flow** (`test_integration.py`): Test failed payout retry functionality

## Running Tests

### Prerequisites

Make sure you have the testing dependencies installed:

```bash
cd backend
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov respx
```

### Run All Tests

```bash
cd backend
./run_tests.sh
```

### Run Specific Test Categories

```bash
# Run unit tests only
python -m pytest tests/test_config.py tests/test_security.py -v

# Run API endpoint tests
python -m pytest tests/test_health.py tests/test_webhooks.py tests/test_payments.py tests/test_payouts.py -v

# Run service tests
python -m pytest tests/test_supabase_service.py tests/test_paystack_service.py -v

# Run integration tests
python -m pytest tests/test_integration.py -v
```

### Run Tests with Coverage

```bash
# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

## Test Fixtures

The test suite provides several useful fixtures in `conftest.py`:

- `client`: FastAPI TestClient for making HTTP requests
- `mock_supabase`: Mocked Supabase service
- `mock_paystack`: Mocked Paystack service
- `sample_transaction_data`: Sample transaction data for testing
- `sample_payout_data`: Sample payout data for testing
- `sample_webhook_data`: Sample webhook data for testing

## Test Coverage Goals

The current test suite aims for 80% code coverage. The configuration in `pyproject.toml` enforces this requirement.

To check current coverage:

```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Adding New Tests

When adding new functionality:

1. Create a new test file following the naming convention `test_*.py`
2. Use appropriate fixtures for mocking dependencies
3. Test both success and failure cases
4. Ensure tests are isolated and don't depend on external services
5. Add assertions to verify expected behavior

## Continuous Integration

The test suite is designed to be run in CI/CD pipelines. The `run_tests.sh` script provides a convenient way to execute all tests with coverage reporting.

## Test Data

Test data is generated using fixtures to ensure consistency and isolation between tests. Sensitive data is mocked and not read from environment variables during testing.

## Mocking Strategy

The test suite uses comprehensive mocking to isolate units under test:

- External API calls (Paystack, Supabase) are mocked
- Database operations are mocked
- Environment variables are controlled through fixtures
- Time-dependent operations use frozen time where appropriate

This ensures tests are fast, reliable, and don't depend on external services or network connectivity.
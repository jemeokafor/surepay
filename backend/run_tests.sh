#!/usr/bin/env bash
# Test runner script for SurePay backend

set -e

echo "🚀 Running SurePay Backend Tests"
echo "================================="

# Activate virtual environment
source venv/bin/activate

# Run tests with coverage
echo "Running unit tests..."
python -m pytest tests/test_config.py tests/test_security.py -v

echo ""
echo "Running API endpoint tests..."
python -m pytest tests/test_health.py tests/test_webhooks.py tests/test_payments.py tests/test_payouts.py -v

echo ""
echo "Running service tests..."
python -m pytest tests/test_supabase_service.py tests/test_paystack_service.py -v

echo ""
echo "Running integration tests..."
python -m pytest tests/test_integration.py -v

echo ""
echo "Running all tests with coverage..."
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Tests completed successfully!"
echo "📊 Coverage report available in htmlcov/index.html"
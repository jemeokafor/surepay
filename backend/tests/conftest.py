import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
import sys

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import the main app
from app.main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_supabase():
    """Mock Supabase service"""
    with patch('app.services.supabase') as mock:
        yield mock

@pytest.fixture
def mock_paystack():
    """Mock Paystack service"""
    with patch('app.services.paystack') as mock:
        yield mock

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        "amount": 10000,
        "currency": "NGN",
        "vendor_id": "test_vendor_id",
        "product_id": "test_product_id",
        "metadata": {"test": "data"}
    }

@pytest.fixture
def sample_payout_data():
    """Sample payout data for testing"""
    return {
        "transaction_id": "test_transaction_id",
        "vendor_id": "test_vendor_id",
        "amount": 9500
    }

@pytest.fixture
def sample_webhook_data():
    """Sample webhook data for testing"""
    return {
        "event": "charge.success",
        "data": {
            "reference": "test_reference",
            "amount": 10000
        }
    }
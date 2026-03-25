import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_payment_initialize_success(client):
    """Test successful payment initialization"""
    # Test data
    transaction_data = {
        "amount": 10000,
        "currency": "NGN",
        "vendor_id": "vendor_123",
        "customer_email": "test@example.com",
        "product_id": "product_123",
        "metadata": {"test": "data"}
    }
    
    # Mock services
    with patch('app.services.supabase.create_transaction', new=AsyncMock(return_value={"id": "txn_123"})), \
         patch('app.services.supabase.update_transaction_paystack_details', new=AsyncMock(return_value=True)), \
         patch('app.services.paystack.initialize_transaction', new=AsyncMock(return_value={
             "status": True,
             "data": {
                 "authorization_url": "https://paystack.com/pay/test",
                 "access_code": "test_access_code"
             }
         })):
        
        response = client.post("/api/payments/initialize", json=transaction_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "authorization_url" in data

def test_payment_initialize_missing_fields(client):
    """Test payment initialization with missing required fields"""
    # Missing customer_email
    transaction_data = {
        "amount": 10000,
        "vendor_id": "vendor_123"
    }
    
    response = client.post("/api/payments/initialize", json=transaction_data)
    
    # Should fail with bad request
    assert response.status_code == 422

def test_payment_verify_success(client):
    """Test successful payment verification"""
    transaction_id = "txn_123"
    
    # Mock services
    with patch('app.services.supabase.get_transaction', new=AsyncMock(return_value={"id": "txn_123"})), \
         patch('app.services.paystack.verify_transaction', new=AsyncMock(return_value={
             "status": True,
             "data": {
                 "status": "success"
             }
         })), \
         patch('app.services.supabase.update_transaction_status', new=AsyncMock(return_value=True)):
        
        response = client.post(f"/api/payments/verify/{transaction_id}")
        
        assert response.status_code == 200

def test_payment_verify_not_found(client):
    """Test payment verification for non-existent transaction"""
    transaction_id = "non_existent"
    
    # Mock services
    with patch('app.services.supabase.get_transaction', new=AsyncMock(return_value=None)):
        response = client.post(f"/api/payments/verify/{transaction_id}")
        
        assert response.status_code == 404
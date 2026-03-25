import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_payout_create_success(client):
    """Test successful payout creation"""
    # Test data
    payout_data = {
        "transaction_id": "txn_123",
        "vendor_id": "vendor_123",
        "amount": 9500
    }
    
    # Mock services
    with patch('app.services.supabase.get_transaction', new=AsyncMock(return_value={
        "id": "txn_123",
        "status": "RELEASED"
    })), \
         patch('app.services.supabase.get_payout_by_transaction', new=AsyncMock(return_value=None)), \
         patch('app.services.supabase.get_vendor', new=AsyncMock(return_value={
             "id": "vendor_123",
             "name": "Test Vendor",
             "bank_account": {
                 "account_number": "1234567890",
                 "bank_code": "058"
             },
             "paystack_recipient_id": "recipient_123"
         })), \
         patch('app.services.paystack.initiate_transfer', new=AsyncMock(return_value={
             "status": True,
             "data": {
                 "id": "transfer_123",
                 "status": "pending"
             }
         })), \
         patch('app.services.supabase.create_payout', new=AsyncMock(return_value={"id": "payout_123"})):
        
        response = client.post("/api/payouts/create", json=payout_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "transfer_id" in data

def test_payout_create_transaction_not_found(client):
    """Test payout creation for non-existent transaction"""
    payout_data = {
        "transaction_id": "non_existent",
        "vendor_id": "vendor_123",
        "amount": 9500
    }
    
    # Mock services
    with patch('app.services.supabase.get_transaction', new=AsyncMock(return_value=None)):
        response = client.post("/api/payouts/create", json=payout_data)
        
        assert response.status_code == 404

def test_payout_create_wrong_status(client):
    """Test payout creation for transaction not in RELEASED status"""
    payout_data = {
        "transaction_id": "txn_123",
        "vendor_id": "vendor_123",
        "amount": 9500
    }
    
    # Mock services
    with patch('app.services.supabase.get_transaction', new=AsyncMock(return_value={
        "id": "txn_123",
        "status": "FUNDS_LOCKED"  # Wrong status
    })):
        response = client.post("/api/payouts/create", json=payout_data)
        
        assert response.status_code == 400

def test_payout_retry_success(client):
    """Test successful payout retry"""
    transaction_id = "txn_123"
    
    # Mock services
    with patch('app.services.supabase.get_payout_by_transaction', new=AsyncMock(return_value={
        "id": "payout_123",
        "status": "FAILED"
    })), \
         patch('app.services.supabase.get_transaction', new=AsyncMock(return_value={
             "id": "txn_123",
             "vendor_id": "vendor_123"
         })), \
         patch('app.services.supabase.get_vendor', new=AsyncMock(return_value={
             "id": "vendor_123",
             "paystack_recipient_id": "recipient_123"
         })), \
         patch('app.services.paystack.initiate_transfer', new=AsyncMock(return_value={
             "status": True,
             "data": {
                 "id": "transfer_456",
                 "status": "pending"
             }
         })), \
         patch('app.services.supabase.update_payout_retry', new=AsyncMock(return_value=True)):
        
        response = client.post(f"/api/payouts/retry/{transaction_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
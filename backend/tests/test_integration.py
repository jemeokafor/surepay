import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

def test_complete_payment_flow(client):
    """Test complete payment flow from initialization to webhook confirmation"""
    # 1. Initialize payment
    transaction_data = {
        "amount": 10000,
        "currency": "NGN",
        "vendor_id": "vendor_123",
        "customer_email": "test@example.com",
        "product_id": "product_123"
    }
    
    with patch('app.services.supabase.create_transaction', new=AsyncMock(return_value={"id": "txn_123"})), \
         patch('app.services.supabase.update_transaction_paystack_details', new=AsyncMock(return_value=True)), \
         patch('app.services.paystack.initialize_transaction', new=AsyncMock(return_value={
             "status": True,
             "data": {
                 "authorization_url": "https://paystack.com/pay/test",
                 "access_code": "test_access_code"
             }
         })):
        
        # Initialize payment
        response = client.post("/api/payments/initialize", json=transaction_data)
        assert response.status_code == 200
        init_data = response.json()
        assert init_data["status"] == "success"
    
    # 2. Simulate Paystack webhook confirmation
    webhook_payload = {
        "event": "charge.success",
        "data": {
            "reference": "txn_123",  # Same as transaction ID
            "amount": 10000
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(webhook_payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    with patch('app.services.supabase.update_transaction_status', new=AsyncMock(return_value=True)):
        # Send webhook
        response = client.post(
            "/api/webhooks/paystack",
            json=webhook_payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200
        webhook_data = response.json()
        assert webhook_data["status"] == "success"

def test_complete_payout_flow(client):
    """Test complete payout flow from creation to webhook confirmation"""
    # 1. Create payout
    payout_data = {
        "transaction_id": "txn_123",
        "vendor_id": "vendor_123",
        "amount": 9500
    }
    
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
        
        # Create payout
        response = client.post("/api/payouts/create", json=payout_data)
        assert response.status_code == 200
        payout_result = response.json()
        assert payout_result["status"] == "success"
    
    # 2. Simulate successful transfer webhook
    webhook_payload = {
        "event": "transfer.success",
        "data": {
            "id": "transfer_123",
            "reference": "txn_123"
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(webhook_payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    with patch('app.services.supabase.update_payout_status', new=AsyncMock(return_value=True)):
        # Send webhook
        response = client.post(
            "/api/webhooks/paystack",
            json=webhook_payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200

def test_failed_payout_and_retry(client):
    """Test failed payout and retry flow"""
    transaction_id = "txn_123"
    
    # 1. Simulate failed transfer webhook
    webhook_payload = {
        "event": "transfer.failed",
        "data": {
            "id": "transfer_123",
            "reference": "txn_123",
            "reason": "Insufficient funds"
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(webhook_payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    with patch('app.services.supabase.update_payout_status', new=AsyncMock(return_value=True)):
        # Send webhook
        response = client.post(
            "/api/webhooks/paystack",
            json=webhook_payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200
    
    # 2. Retry payout
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
        
        # Retry payout
        response = client.post(f"/api/payouts/retry/{transaction_id}")
        assert response.status_code == 200
        retry_result = response.json()
        assert retry_result["status"] == "success"
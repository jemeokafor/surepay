import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock

def test_webhook_paystack_success(client):
    """Test successful Paystack webhook handling"""
    # Create test payload
    payload = {
        "event": "charge.success",
        "data": {
            "reference": "test_ref_123",
            "amount": 10000
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    # Mock Supabase service
    with patch('app.services.supabase.update_transaction_status', new=AsyncMock(return_value=True)):
        # Send request with signature header
        response = client.post(
            "/api/webhooks/paystack",
            json=payload,
            headers={"x-paystack-signature": signature}
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

def test_webhook_paystack_invalid_signature(client):
    """Test Paystack webhook with invalid signature"""
    payload = {
        "event": "charge.success",
        "data": {
            "reference": "test_ref_123",
            "amount": 10000
        }
    }
    
    # Send request with invalid signature
    response = client.post(
        "/api/webhooks/paystack",
        json=payload,
        headers={"x-paystack-signature": "invalid_signature"}
    )
    
    # Should fail authentication
    assert response.status_code == 401

def test_webhook_paystack_transfer_success(client):
    """Test Paystack transfer.success webhook"""
    payload = {
        "event": "transfer.success",
        "data": {
            "id": "transfer_123",
            "reference": "test_ref_123"
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    # Mock Supabase service
    with patch('app.services.supabase.update_payout_status', new=AsyncMock(return_value=True)):
        response = client.post(
            "/api/webhooks/paystack",
            json=payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200

def test_webhook_paystack_transfer_failed(client):
    """Test Paystack transfer.failed webhook"""
    payload = {
        "event": "transfer.failed",
        "data": {
            "id": "transfer_123",
            "reference": "test_ref_123",
            "reason": "Insufficient funds"
        }
    }
    
    # Create signature
    import hashlib
    import hmac
    signature = hmac.new(
        b"test_webhook_secret",
        json.dumps(payload).encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    # Mock Supabase service
    with patch('app.services.supabase.update_payout_status', new=AsyncMock(return_value=True)):
        response = client.post(
            "/api/webhooks/paystack",
            json=payload,
            headers={"x-paystack-signature": signature}
        )
        
        assert response.status_code == 200
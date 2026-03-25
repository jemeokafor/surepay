import pytest
import hashlib
import hmac
import json
from unittest.mock import Mock
from app.core.security import verify_paystack_signature, verify_paystack_webhook

def test_verify_paystack_signature_valid():
    """Test valid Paystack signature verification"""
    # Create test payload and secret
    payload = b'{"test": "data"}'
    secret = "test_secret_key"
    
    # Create expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    # Verify the signature
    result = verify_paystack_signature(payload, expected_signature)
    assert result is True

def test_verify_paystack_signature_invalid():
    """Test invalid Paystack signature verification"""
    payload = b'{"test": "data"}'
    secret = "test_secret_key"
    wrong_signature = "wrong_signature"
    
    # Create expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    # Verify with wrong signature
    result = verify_paystack_signature(payload, wrong_signature)
    assert result is False

def test_verify_paystack_signature_empty():
    """Test signature verification with empty values"""
    result = verify_paystack_signature(b'', '')
    assert result is False

# Note: verify_paystack_webhook requires async/await and FastAPI request objects
# We'll test this in integration tests
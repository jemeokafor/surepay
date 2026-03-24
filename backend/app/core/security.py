import hashlib
import hmac
import json
from fastapi import HTTPException, Header, Request
from app.core.config import settings

def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Paystack webhook signature to ensure authenticity
    """
    # Create HMAC signature using webhook secret
    expected_signature = hmac.new(
        settings.PAYSTACK_WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)

async def get_raw_body(request: Request) -> bytes:
    """
    Get raw request body for signature verification
    """
    return await request.body()

def verify_paystack_webhook(payload: dict, signature: str) -> bool:
    """
    Verify Paystack webhook with additional validation
    """
    # Check if signature matches
    if not verify_paystack_signature(json.dumps(payload).encode('utf-8'), signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Additional validation can be added here
    return True